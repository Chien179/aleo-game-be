
from sqlalchemy.ext.asyncio import async_sessionmaker, async_scoped_session, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Query, declarative_base, load_only, defer 
from sqlalchemy import Delete, Insert, Update, select, Select, update, insert, delete, inspect
from sqlalchemy.sql import func

from redis.asyncio import Redis
from redis.asyncio.cluster import RedisCluster
from typing import Any, Dict, Type, Union
from asyncio import current_task, Task
from src.lib.exception import InternalServer
from src.lib.logger import logger
from src.lib.cache import Cache
from datetime import datetime, timezone
from typing import List, Dict
from urllib.parse import urlparse
from functools import wraps
from starlette.background import BackgroundTask
from contextvars import ContextVar, Token
from uuid import uuid4

import traceback
import json

session_context: ContextVar[str] = ContextVar("session_context")

def get_session_context() -> str:
    return session_context.get()

def set_session_context() -> Token:
    return session_context.set(str(uuid4()))

def reset_session_context(context: Token) -> None:
    logger.debug("reset context session db")
    session_context.reset(context)

def current_time():
    return datetime.now(tz=timezone.utc)

Base = declarative_base()


def deserialize(func):
    """
    The `deserialize` function is a decorator that formats datetime objects in the result of an async
    function to a specific string format.
    
    :param func: The `func` parameter is a function that will be decorated by the `deserialize`
    decorator
    :return: The `deserialize` function returns a decorated version of the input function `func`.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        _projection = kwargs.get('projection', [])
        _should_load_data = kwargs.get('should_load_data', True)
        _result = await func(*args, **kwargs)
        if not _result:
            return _result
        
        def formatter(data: dict):
            for key, value in data.copy().items():
                if isinstance(value, datetime):
                    data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                if key in _projection and not _should_load_data:
                    del data[key]
            return data
        if isinstance(_result, list):
            _result = list(map(formatter, _result))
        else:
            _result = formatter(_result)
        return _result
    return wrapper


class PostgresClient(Cache):

    def __init__(self, model: Type[Base], session: async_scoped_session, redis: Union[Redis, None] = None, *args, **kwargs) -> None:
        super(PostgresClient, self).__init__(redis, *args, **kwargs)
        self.model = model
        self.session = session
        self.redis = redis
        self._table_name = self.model.__tablename__

    def get_key(self, filter: Dict) -> str:
        return f'{self._table_name}.{super().get_key(filter)}'

    def cache_key(self, filter: Dict):
        _key_items = [f'{k}:{v}' for k, v in filter.items()]
        return f'{self._table_name}.{".".join(_key_items)}'

    @deserialize
    async def find_one(self, filter: Union[Dict, Select], projection: List[str] = [], should_load_data: bool = True,from_cache: bool = False, cache: bool = False, *args, **kwargs) -> Dict:
        """
        The `find_one` function retrieves a single document from a database based on a filter, with an
        option to retrieve from cache and store in cache.
        
        :param filter: The `filter` parameter is used to specify the conditions for filtering the data.
        It can be either a dictionary or a `Select` object. If it is a dictionary, it is used to filter
        the data using the `filter_by` method. If it is a `Select` object, it
        :type filter: Union[Dict, Select]
        :param projection: The `projection` parameter is a list of strings that specifies which fields
        to include in the result. Only the fields specified in the `projection` list will be returned in
        the result. If the `projection` list is empty, all fields will be included in the result
        :type projection: List[str]
        :param from_cache: The `from_cache` parameter is a boolean flag that indicates whether to
        retrieve the result from a cache or not. If set to `True`, the function will first check if the
        result exists in the cache and return it if found. If not found, it will proceed to execute a
        query to fetch, defaults to False
        :type from_cache: bool (optional)
        :param cache: The `cache` parameter is a boolean flag that determines whether the result of the
        query should be cached or not. If set to `True`, the result will be stored in the cache for
        future use. If set to `False`, the result will not be cached, defaults to False
        :type cache: bool (optional)
        :return: The function `find_one` returns a dictionary.
        """
        _result = None
        if from_cache:
            assert not isinstance(
                filter, Select), "filter from cache must be dictionary"
            _result = self.get(filter)
        if not _result:
            _query = None
            if isinstance(filter, Select):
                _query = filter.limit(1)
            else:
                _query = select(self.model).filter_by(**filter).limit(1)
            if len(projection):
                columns = [getattr(self.model, i) for i in projection]
                _query = (
                    _query.options(load_only(*columns)) if should_load_data
                    else _query.options(*[defer(getattr(self.model, i)) for i in projection] )
                )
            _obj = await self.session.execute(_query)
            _obj = _obj.scalars().fetchall()
            if len(_obj) == 0:
                return None
            _obj = _obj[0]
            if len(projection):
                if should_load_data: _result = {c: getattr(_obj, c) for c in projection}
                else:  _result = {k: v for (k, v) in _obj.__dict__.items()
                                if k != '_sa_instance_state'}
            else:
                _result = _obj if not _obj else _obj.as_dict
        else:
            _result = json.loads(_result)
        if cache:
            assert isinstance(
                filter, dict), "filter save in cache must be dictionary. Select will be update in next version"
            self.set(filter, _result, ttl=-1)
        return _result

    @deserialize
    async def find(self, filter: Union[Dict[str, Any], Select], projection: List[str] = [], should_load_data: bool = True,limit: int = 0, skip: int = 0,from_cache: bool = False, hset_key: Union[str, None] = None, cache: bool = False, *args, **kwargs) -> List[Dict]:
        """
        The `find` function retrieves data from a cache or a database based on a filter, projection, and
        caching options, and returns the results as a list of dictionaries.
        
        :param filter: The `filter` parameter is used to specify the conditions for filtering the data.
        It can be either a dictionary or a `Select` object. If it is a dictionary, it represents
        key-value pairs where the keys are the column names and the values are the desired values for
        those columns. If it
        :type filter: Union[Dict[str, Any], Select]
        :param projection: The `projection` parameter is a list of strings that specifies which fields
        or columns to include in the result. Only the specified fields will be returned in the resulting
        dictionaries. If `projection` is empty, all fields will be included in the result
        :type projection: List[str]
        :param from_cache: The `from_cache` parameter is a boolean flag that indicates whether the data
        should be retrieved from a cache or not. If set to `True`, the function will try to retrieve the
        data from a cache using the provided filter. If the data is not found in the cache, it will
        proceed to, defaults to False
        :type from_cache: bool (optional)
        :param hset_key: The `hset_key` parameter is used to specify the key under which the result will
        be stored in a cache. It is a string value that represents the key
        :type hset_key: Union[str, None]
        :param cache: The `cache` parameter is a boolean flag that determines whether the results of the
        query should be cached or not. If set to `True`, the results will be cached using the `hset`
        method. If set to `False`, the results will not be cached, defaults to False
        :type cache: bool (optional)
        :return: a list of dictionaries.
        """
        _result = []
        if from_cache:
            assert isinstance(
                filter, dict), "filter from cache must be dictionary. Select object will be update next version"
            _result = self.hget_all(filter)
        if not _result:
            _query = None
            if isinstance(filter, Select):
                _query = filter if limit == 0 else filter.limit(limit)
                _query = _query if skip == 0 else _query.offset(skip)
            else:
                if limit == 0:
                    _query = select(self.model).filter_by(**filter)
                else: _query = select(self.model).filter_by(**filter).limit(limit)
                if skip != 0:
                    _query = _query.offset(skip)
            if len(projection): 
                columns = [getattr(self.model, i) for i in projection]
                _query = (
                    _query.options(load_only(*columns)) if should_load_data
                    else _query.options(*[defer(getattr(self.model, i)) for i in projection] )
                )
            _obj = await self.session.execute(_query)
            _obj = _obj.scalars().fetchall()
            if len(projection):
                if should_load_data:
                    for o in _obj:
                        _result.append({c: getattr(o, c) for c in projection})
                else: 
                    for item in _obj:
                        item = {k: v for (k, v) in item.__dict__.items()
                                if k != '_sa_instance_state'}
                        _result.append(item)
            else:
                _result = [] if not _obj else [i.as_dict for i in _obj]
        else:
            _temp = [json.loads(i) for i in _result.values()]
            _result = []
            for i in _temp:
                _result.extend(i)
        if cache:
            if not hset_key:
                raise InternalServer(
                    errors={'hset_key': 'not provide with cache=True'})
            assert isinstance(
                filter, dict), "filter save to cache must be dictionary. Select object will be udpated to next version"
            self.hset(filter, hset_key, _result)
        return _result

    async def _iud(self, _orm):
        _orm = _orm.returning(self.model.id)
        _result = await self.session.execute(_orm)
        return _result.all()

    async def insert(self, data: Union[Dict, List[Dict], Insert], background: bool = False):
        """
        The `insert` function inserts data into a database table, and can be executed in the background
        if specified.
        
        :param data: The `data` parameter can be either a dictionary, a list of dictionaries, or an
        instance of the `Insert` class. It represents the data that you want to insert into the database
        :type data: Union[Dict, List[Dict], Insert]
        :param background: The `background` parameter is a boolean flag that determines whether the
        insertion operation should be executed in the background or not. If set to `True`, the insertion
        operation will be executed in the background using a `BackgroundTask` object. If set to `False`
        (default), the insertion operation will, defaults to False
        :type background: bool (optional)
        :return: a boolean value. If the `background` parameter is set to `True`, it returns `True` if
        the background task is successfully executed, and `False` if there is an exception. If the
        `background` parameter is set to `False`, it returns the result of the `insert` function.
        """
        _insert = insert(self.model).values(
            data) if isinstance(data, dict) else data
        async def func():
            _res = await self._iud(_insert)
            await self.session.commit()
            return _res
        if background:
            try:
                await BackgroundTask(func)()
                return True
            except:
                traceback.print_exc()
                return False
        return await func()

    async def update(self, filter: Union[Dict, Update], data: Dict, background: bool = False):
        """
        The `update` function updates a model with the given filter and data, and optionally runs the
        update in the background.
        
        :param filter: The `filter` parameter is used to specify the conditions for selecting the rows
        to be updated in the database. It can be either a dictionary or an instance of the `Update`
        class. If it is a dictionary, it is used to filter the rows based on the key-value pairs. If it
        :type filter: Union[Dict, Update]
        :param data: The `data` parameter is a dictionary that contains the updated values for the
        specified fields in the database table
        :type data: Dict
        :param background: The `background` parameter is a boolean flag that determines whether the
        update operation should be executed in the background or not. If `background` is set to `True`,
        the update operation will be executed asynchronously in the background using a `BackgroundTask`.
        If `background` is set to `False`, defaults to False
        :type background: bool (optional)
        :return: a boolean value. If the `background` parameter is set to `True`, it returns `True` if
        the background task is executed successfully, and `False` if there is an exception. If the
        `background` parameter is set to `False`, it returns the result of the `update` function.
        """
        _update = update(self.model).filter_by(
            **filter).values(data) if isinstance(filter, dict) else filter
        async def func():
            _res = await self._iud(_update)
            await self.session.commit()
            return _res
        if background:
            try:
                await BackgroundTask(func)()
                return True
            except:
                traceback.print_exc()
                return False
        return await func()

    async def delete(self, filter: Union[Dict, Delete], background: bool = False):
        """
        The `delete` function deletes records from a database table based on a given filter, and can be
        executed in the background if specified.
        
        :param filter: The `filter` parameter is used to specify the conditions for deleting records
        from the database. It can be either a dictionary or an instance of the `Delete` class. If it is
        a dictionary, it will be used to filter the records to be deleted using the `filter_by` method.
        If
        :type filter: Union[Dict, Delete]
        :param background: The `background` parameter is a boolean flag that determines whether the
        deletion operation should be executed in the background or not. If set to `True`, the deletion
        operation will be executed in the background using a `BackgroundTask`. If set to `False`, the
        deletion operation will be executed synchronously, defaults to False
        :type background: bool (optional)
        :return: a boolean value. If the `background` parameter is set to `True`, it returns `True` if
        the background task is successfully executed, and `False` if there is an exception. If the
        `background` parameter is set to `False`, it returns the result of the `delete` function.
        """
        _delete = delete(self.model).filter_by(
            **filter) if isinstance(filter, dict) else filter
        async def func():
            _res = await self._iud(_delete)
            await self.session.commit()
            return _res
        if background:
            try:
                await BackgroundTask(func)()
                return True
            except:
                traceback.print_exc()
                return False
        return await func()
    
    async def count(self, filter: Union[Dict, Select]) -> int:
        """
        The `count` function returns the number of records that match a given filter.
        
        :param filter: The `filter` parameter can be either a dictionary or a `Select` object
        :type filter: Union[Dict, Select]
        :return: The count of the objects that match the given filter criteria.
        """
        if isinstance(filter, Select):
            _obj = await self.session.scalar(filter)
        else:
            _obj = (await self.session
                    .execute(select(func.count())
                                .select_from(select(self.model)
                                    .filter_by(**filter)))).scalar()
        return _obj

class Model(Base):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    @property
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def apply(cls, session: async_scoped_session, redis: Union[Redis, RedisCluster, None]) -> PostgresClient:
        return PostgresClient(cls, session, redis)

class Postgres:

    engine = None

    def __init__(self, url: str, *args, **kwargs) -> None:
        super(Postgres, self).__init__(*args, ** kwargs)
        self.Model = Model
        self.url = url

    def __current_task(self) -> Task:
        task = current_task()
        if not task:
            raise RuntimeError("No currently active asyncio.Task found")
        return task
    
    def connect(self, **kwargs):
        if Postgres.engine is None:
            Postgres.engine = create_async_engine(url=self.url, **kwargs)
            try:
                parsed = urlparse(self.url)
                url_replaced = parsed._replace(netloc="{}:{}@{}:{}".format(parsed.username, "******", parsed.hostname, parsed.port))
                logger.debug(f"Database connected: {url_replaced.geturl()}")
            except:
                logger.debug("Database connected")
        else:
            logger.warning("connection is created")
    
    async def disconnect(self):
        await self.session.close()
        await self.engine.dispose()
        logger.debug(f"Database disconnected")

    def make_session(self, options: dict = {}, scope = None):
        options.setdefault("class_", AsyncSession)
        options.setdefault("query_cls", Query)
        factory = async_sessionmaker(bind=Postgres.engine, **options)
        self.session = async_scoped_session(factory, self.__current_task if not scope else scope)()

    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(self.Model.metadata.create_all)

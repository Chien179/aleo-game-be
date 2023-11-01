from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from redis.asyncio.cluster import RedisCluster
from bson import ObjectId
from typing import Optional, Dict, Union, List
from src.lib.cache import Cache
from starlette.background import BackgroundTask
from datetime import datetime, timezone
from urllib.parse import urlparse
from functools import wraps
from bson import ObjectId
import copy

def current_time():
    return datetime.now(tz=timezone.utc)

def deserialize(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        _result = await func(*args, **kwargs)
        if not _result:
            return _result
        def formater(data:dict):
            for k, v in data.copy().items():
                if isinstance(v, ObjectId):
                    data[k] = str(v)
                elif isinstance(v, datetime):
                    data[k] = int(v.timestamp())
            return data
        if isinstance(_result, list):
            _result = list(map(formater, _result))
        else:
            _result = formater(_result)
        return _result
    return wrapper

class MongoCollection(Cache):

    def __init__(self, collection, prefix_key: str = "", redis: Union[Redis, RedisCluster, None ] = None, *args, **kwargs) -> None:
        super(MongoCollection, self).__init__(redis, *args, **kwargs)
        self.collection = collection
        self.prefix_key = prefix_key
        self.redis = redis

    def get_key(self, filter: Dict) -> str:
        return self.prefix_key+':'+super().get_key(filter)

    @deserialize
    async def find_one(self, filter: Dict, projection: Dict = {}, with_cache=False):
        if with_cache:
            assert self.redis, "Redis not set"
            _key = self.get_key(filter)
            _data = self.redis.get(_key)
            return _data
        item = await self.collection.find_one(filter=filter, projection=projection)
        return item

    @deserialize
    async def find(self, filter: Dict, projection: Dict = {}, sort: Optional[bool] = True, limit: Optional[Union[int, None]] = None, skip: Optional[int] = 0,with_cache: Optional[bool] = False):
        sort_type = 1
        if not sort: sort_type = -1
        students = await self.collection.find(filter=filter, projection=projection).sort('created_at', sort_type).skip(skip).to_list(limit)
        return students

    async def insert_one(self, data: Dict, background: bool = False):
        _keys = list(data.keys())
        if 'created_at' not in _keys:
            data['created_at'] = current_time()
        if 'updated_at' not in _keys:
            data['updated_at'] = current_time()
        _data = copy.deepcopy(data)
        async def func():
            return await self.collection.insert_one(_data)
        if background:
            await BackgroundTask(func)()
            return True
        return await func()
    
    async def insert_many(self, data: List[Dict], background: bool = False):
        async def func():
            return await self.collection.insert_many(data)
        if background:
            await BackgroundTask(func)()
            return True
        return await func()

    async def delete_by_id(self, id: str, background: Optional[bool] = False):
        async def func():
            if not isinstance(id, ObjectId):
                _id = ObjectId(id)
            return await self.collection.delete_one({'_id': _id})
        if background:
            await BackgroundTask(func)()
            return True
        delete_result = await self.collection.delete_one({"_id": ObjectId(id)})
        return delete_result

    async def delete_many(self, filter: Dict, background: Optional[bool] = False):
        async def func():
            if '_id' in filter.keys():
                _id = filter.get('_id')
                if isinstance(_id, ObjectId):
                    filter['_id'] = str(_id)
            return await self.collection.delete_many(filter)
        if background:
            await BackgroundTask(func)()
            return True
        return await func()

    async def delete_one(self, filter:Dict, background: bool = False):
        async def func():
            return await self.collection.delete_one(filter)
        if background:
            await BackgroundTask(func)()
            return True
        return func()

    async def update(self, filter: Dict, data: Dict, background: Optional[bool] = False):
        _keys = list(data.keys())
        if 'updated_at' not in _keys:
            data['updated_at'] = current_time()
        data = {'$set': data}
        async def func():
            if '_id' in filter.keys():
                _id = filter.get('_id')
                if isinstance(_id, ObjectId):
                    filter['_id'] = str(_id)
            await self.collection.update_many(filter=filter, update=data)

        if background:
            await BackgroundTask(func)()
            return True

        return await func()

    async def count(self, filter:Dict) -> int:
        return await self.collection.count_documents(filter)

    async def create_index(self, index_models: List[tuple], index_name):
        existing_indexes = await self.collection.index_information()         
        if index_name in existing_indexes:
            return
        return await self.collection.create_index(index_models, name=index_name)        



class MongoClient:

    def __init__(self, uri: str, db_name:Optional[str]=None, *args, **kwargs):
        super(MongoClient, self).__init__(*args, **kwargs)
        url_parts = urlparse(uri)
        url_db = url_parts.path.strip("/")
        self.client = self.connect(uri)
        if not db_name and not url_db:
            self.database = None
        else:
            self.database = self.get_database(db_name if db_name else url_db)

    def connect(self, mongo_uri: str, config: dict = {}):
        client = AsyncIOMotorClient(mongo_uri, **config)
        return client

    def get_database(self, name):
        return self.client.get_database(name)
    
    def set_database(self, name):
        self.database = self.client.get_database(name)

    def collection(self, name, config: Dict={}) -> MongoCollection:
        col = self.database[name]
        dao = MongoCollection(col, **config)
        return dao

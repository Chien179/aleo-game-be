from celery import Celery
from src.config import config
from src.connect import database, redis
from src.lib.models import VaAccount, Bank, VaTransaction
from src.lib.logger import logger
from src.lib.postgres import get_session_context, set_session_context
import json
import asyncio

set_session_context()

class AsyncCelery(Celery):

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance') or not cls.instance:
          cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.patch_task()
        database.connect(pool_size=5, max_overflow=10, pool_recycle=7200, echo_pool="debug")
        database.make_session(scope=get_session_context)
        asyncio.run(self.init_redis())
        self.redis = redis
        self.va_account = VaAccount.apply(database.session, None)
        self.bank = Bank.apply(database.session, None)
        self.va_transaction = VaTransaction.apply(database.session, None)

    async def init_redis(self):
        await redis.connect()

    def patch_task(self):
        TaskBase = self.Task
        class ContextTask(TaskBase):
            abstract = True
            loop = asyncio.new_event_loop()
            def _run(self, *args, **kwargs):
                result = self.loop.run_until_complete(
                    TaskBase.__call__(self, *args, **kwargs)
                )
                return result
            def __call__(self, *args, **kwargs):
                return self._run(*args, **kwargs)
        self.Task = ContextTask


def create_worker():
    _celery = AsyncCelery(__name__, broker=config.BROKER_URL, backend=config.BROKER_URL)
    _conf_json = json.loads(config.model_dump_json())
    _celery.conf.update(_conf_json)
    return _celery


worker = create_worker()

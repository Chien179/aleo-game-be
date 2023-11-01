from src.lib.mongo import MongoClient
from src.config import config
from src.lib.http import AsyncHttpClient
from src.lib.cache import Cache

mongo_client = MongoClient(config.URI, config.DB_NAME)

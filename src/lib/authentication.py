from starlette.requests import Request
from src.lib.exception import Forbidden
from src.lib.enum import APIResponseCode, VARole
from abc import ABC, abstractmethod
from src.lib.logger import logger
from src.lib.postgres import PostgresClient
import datetime
import jwt
import traceback



class Authorization(ABC):

    @abstractmethod
    def validate(self, request: Request, *arg, **kwargs):
        pass


class JsonWebToken(Authorization):
    def __init__(self, key, algorithm, *args, **kwargs) -> None:
        super(JsonWebToken, self).__init__(*args, **kwargs)
        self.key = key
        self.algorithm = algorithm

    def create_token(self, payload_data, *arg, **kwargs): 
        token  = jwt.encode(payload={
            "payload": payload_data,
            "exp":datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, key=self.key, algorithm=self.algorithm)
        refresh_token = jwt.encode(payload={
            "payload": payload_data,
            "exp":datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, key=self.key, algorithm=self.algorithm)
        return {
            "token": token,
            "refresh_token": refresh_token
        }

    def validate(self, request: Request, *arg, **kwargs):
        super(JsonWebToken, self).validate(request, *arg, **kwargs)
        try:
            _authorization = request.headers.get('authorization')
            if not _authorization:
                raise
            _type, _token = _authorization.split()
            if _type.lower() != 'bearer':
                raise
            _decode = jwt.decode(_token, key=self.key,
                                    algorithms=[self.algorithm])
            return _decode.get('payload')
        except:
            traceback.print_exc()
            raise Forbidden(code=APIResponseCode.OPT_EXPIRED.value["code"])

    def refresh_token(self, refresh_token):
        try: 
            _decode = jwt.decode(refresh_token, key=self.key,
                                    algorithms=self.algorithm)
            token  = jwt.encode(payload={
                    "payload": _decode.get("payload"),
                    "exp":datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
                }, key=self.key, algorithm=self.algorithm)
            return token
        except: 
            raise Forbidden(code=APIResponseCode.FORBIDDEN.value["code"])



class APIKeyAuthen(Authorization):

    def __init__(self) -> None:
        super().__init__()
    
    async def validate(self, request: Request, *arg, **kwargs):
        try:
            api_db: PostgresClient = request.state._state.get("api_key")
            if api_db is None:
                logger.error("api db not set")
                raise
            api_key = request.headers.get('authorization')
            _data = await api_db.find_one({"api_key": api_key})
            if not _data:
                logger.error("===== error api_key =====")
                logger.error(api_key)
                logger.error(_data)
                raise Exception()
            if not VARole.check_role(_data.get("role")):
                raise Forbidden(code=APIResponseCode.FORBIDDEN.value["code"], msg="Not found role")
            return _data
        except:
            traceback.print_exc()
            raise Forbidden(code=APIResponseCode.FORBIDDEN.value["code"])
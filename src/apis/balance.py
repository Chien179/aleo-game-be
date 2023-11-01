from starlette.endpoints import HTTPEndpoint
from src.lib.executor import executor
from src.schema.balance import GetBalance, ChangeBalance
from src.helper.balance import BalanceHelper
from src.lib.cache import Cache

_helper = BalanceHelper()


class BalanceAPI(HTTPEndpoint):
    @executor(form_data=ChangeBalance)
    async def post(self, form_data: dict):
        _result = await _helper.change_balance(form_data)
        return _result

    @executor(query_params=GetBalance)
    async def get(self, query_params: dict):
        _result = await _helper.get_balance(query_params)
        return _result

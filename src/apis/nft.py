from starlette.endpoints import HTTPEndpoint
from src.lib.executor import executor
from src.schema.nft import AddNFT, ShowNFT
from src.helper.nft import NFTHelper
from src.lib.cache import Cache

_helper = NFTHelper()


class NFTAPI(HTTPEndpoint):
    @executor(form_data=AddNFT)
    async def post(self, form_data: dict):
        _result = await _helper.add_nft(form_data)
        return _result

    @executor(query_params=ShowNFT)
    async def get(self, query_params: dict):
        _result = await _helper.show_nft(query_params)
        return _result

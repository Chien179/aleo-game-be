from src.lib.exception import NotFound
from src.models import nft_collection


class NFTHelper:
    def __init__(self) -> None:
        pass

    async def add_nft(self, data: dict) -> str:
        await nft_collection.insert_one(data)

        return "success"

    async def show_nft(self, query_params: dict) -> dict:
        nft = await nft_collection.find(filter={"address": query_params.get("address")})

        if not nft:
            raise NotFound(errors="Not found address")

        return nft

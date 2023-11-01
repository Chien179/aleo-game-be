from src.lib.exception import NotFound
from src.models import balance_collection


class BalanceHelper:
    def __init__(self) -> None:
        pass

    async def change_balance(self, data: dict) -> str:
        address = data.get("address")
        amount = data.get("amount")
        method = data.get("method")

        balance = await balance_collection.find_one(filter={"address": address})
        if not balance:
            if not amount:
                amount = 0
            data = {"address": address, "amount": amount}
            await balance_collection.insert_one(data)
        elif method == "+":
            await balance_collection.update(
                filter={"address": address},
                data={"amount": balance.get("amount") + amount},
            )
        else:
            await balance_collection.update(
                filter={"address": address},
                data={"amount": balance.get("amount") - amount},
            )

        return "success"

    async def get_balance(self, query_params: dict) -> dict:
        balance = await balance_collection.find_one(
            filter={"address": query_params.get("address")}
        )

        if not balance:
            raise NotFound(errors="Not found address")

        return balance

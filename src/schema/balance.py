from pydantic import BaseModel
from typing import Optional


class ChangeBalance(BaseModel):
    address: str
    amount: int
    method: str


class GetBalance(BaseModel):
    address: str

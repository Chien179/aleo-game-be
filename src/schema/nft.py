from pydantic import BaseModel
from typing import Optional


class ShowNFT(BaseModel):
    address: str


class AddNFT(BaseModel):
    address: str
    nft_id: str
    base_url: str

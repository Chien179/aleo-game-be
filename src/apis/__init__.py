from starlette.routing import Route, Mount
from src.apis.health_check import HealthCheck
from src.apis.balance import BalanceAPI
from src.apis.nft import NFTAPI

routes = [
    Route("/health_check", HealthCheck),
    Route("/balance", BalanceAPI),
    Route("/nft", NFTAPI),
]

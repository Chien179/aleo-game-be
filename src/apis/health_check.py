from starlette.endpoints import HTTPEndpoint
from src.lib.executor import executor


class HealthCheck(HTTPEndpoint):
    @executor()
    async def get(self):
        return "health check"

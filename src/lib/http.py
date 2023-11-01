import httpx
from functools import wraps

def process(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        args = list(args)
        _url:str = ""
        if len(args) > 1: 
            _url = args[1]
        else:
            _url = kwargs.get("url")
            args.append("")
            del kwargs["url"]
        if _url.startswith("/"):
            _url = _url[1:]
        args[1] = _url
        _result = await func(*args, **kwargs)
        return _result
    return wrapper


class AsyncHttpClient:

    def __init__(self, base_url: str) -> None:
        self.client = httpx.AsyncClient()
        if not base_url.endswith('/'):
            base_url = base_url + '/'
        self.base_url = httpx.URL(base_url)

    @process
    async def get(self, url, params={}, headers={}) -> httpx.Response:
        _response = await self.client.get(self.base_url.join(url), params=params, headers=headers)
        return _response

    @process
    async def post(self, url, data={}, headers={}) -> httpx.Response: 
        _response = await self.client.post(self.base_url.join(url), json=data, headers=headers)
        return _response
    @process
    async def put(self, url, data={}, headers={}) -> httpx.Response:
        _response = await self.client.put(self.base_url.join(url), json=data, headers=headers)
        return _response
    @process
    async def delete(self, url, data={}, headers={}) -> httpx.Response:
        _response = await self.client.delete(self.base_url.join(url), json=data, headers=headers)
        return _response

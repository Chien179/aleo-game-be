from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from src.apis import routes
from src.lib.logger import DefaultFormatter
import json
import logging


class Application(Starlette):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        async def exc_method_not_allow(request: Request, exc: HTTPException):
            return Response(
                content=json.dumps(
                    {"data": "", "msg": "Method not allow", "error": {}}
                ),
                status_code=405,
                headers={"Content-type": "application/json"},
            )

        async def exc_not_found(request: Request, exc: HTTPException):
            return Response(
                content=json.dumps({"data": "", "msg": "Not found", "error": {}}),
                status_code=404,
                headers={"Content-type": "application/json"},
            )

        _excs = self.exception_handlers
        self.exception_handlers = {
            **_excs,
            405: exc_method_not_allow,
            404: exc_not_found,
        }


app = Application(routes=routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger("uvicorn.access")
    logger.setLevel(logging.DEBUG)
    formatter = DefaultFormatter(
        fmt="%(levelprefix)s %(asctime)s [%(process)s] %(message)s",
        use_colors=True,
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@app.on_event("shutdown")
async def app_shutdown():
    pass

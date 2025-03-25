import json
import logging.config
from json import JSONDecodeError
from typing import Callable, Mapping

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.status import HTTP_400_BAD_REQUEST

from webhook import config as cfg
from webhook.core.sync import sync
from webhook.addons.certmanager.main import sync_certificate
from webhook.logconf import LOG_CONF

_LOGGER = logging.getLogger(__name__)


def build_webhook(sync_func: Callable[[Mapping], Mapping]):
    async def webhook(request: Request):
        try:
            body = await request.json()
            _LOGGER.debug(f"Webhook request:\n {json.dumps(body)}")
            response = sync_func(body)
        except JSONDecodeError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse request body: {repr(e)}",
            )
        except KeyError as e:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Missing field from request: {repr(e)}",
            )

        _LOGGER.debug(f"Webhook response:\n {json.dumps(response)}")
        return JSONResponse(response)

    return webhook


async def status(request):
    return JSONResponse({"status": "UP"})


routes = [
    Route("/sync", endpoint=build_webhook(sync), methods=["POST"]),
    Route(
        "/addons/certmanager/sync",
        endpoint=build_webhook(sync_certificate),
        methods=["POST"],
    ),
    Route("/status", endpoint=status, methods=["GET"]),
]


logging.config.dictConfig(LOG_CONF)

if cfg.DEBUG:
    _LOGGER.warning("Running server with debug mode. NOT SUITABLE FOR PRODUCTION!")

app = Starlette(debug=cfg.DEBUG, routes=routes)

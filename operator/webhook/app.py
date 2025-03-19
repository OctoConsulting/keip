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

COMPOSITE_CONTROLLER = "CompositeController"

DECORATOR_CONTROLLER = "DecoratorController"

INTEGRATION_ROUTES_RESOURCE = "integrationroutes"

CERTIFICATES_RESOURCE = "certificates"


async def webhook(request: Request):
    try:
        body = await request.json()
        _LOGGER.debug(f"Webhook request:\n {json.dumps(body)}")
        if _create_integration_route_resources(body):
            _LOGGER.debug("Creating IntegrationRoute resources...")
            # Request API for CompositeController at https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook-request
            response = sync(body["parent"])
        elif _attach_certificate_to_integration_route(body):
            _LOGGER.debug("Attaching a Certificate to an IntegrationRoute...")
            # Request API at for DecoratorController at https://metacontroller.github.io/metacontroller/api/decoratorcontroller.html#sync-hook-request
            response = sync_certificate(body["object"])
        else:
            _LOGGER.error(f"Unknown request:\n {json.dumps(body)}")
    except JSONDecodeError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Failed to parse request body"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Missing field from request: {repr(e)}",
        )

    _LOGGER.debug(f"Webhook response:\n {json.dumps(response)}")
    return JSONResponse(response)


def _create_integration_route_resources(body) -> bool:
    return (
        body["controller"]["kind"] == COMPOSITE_CONTROLLER
        and body["controller"]["spec"]["parentResource"]["resource"]
        == INTEGRATION_ROUTES_RESOURCE
    )


def _attach_certificate_to_integration_route(body) -> bool:
    return (
        body["controller"]["kind"] == DECORATOR_CONTROLLER
        and body["controller"]["spec"]["resources"][0]["resource"]
        == INTEGRATION_ROUTES_RESOURCE
        and body["controller"]["spec"]["attachments"][0]["resource"]
        == CERTIFICATES_RESOURCE
    )


async def status(request):
    return JSONResponse({"status": "UP"})


routes = [
    Route("/sync", endpoint=webhook, methods=["POST"]),
    Route(
        "/addons/certmanager/sync",
        endpoint=webhook,
        methods=["POST"],
    ),
    Route("/status", endpoint=status, methods=["GET"]),
]


logging.config.dictConfig(LOG_CONF)

if cfg.DEBUG:
    _LOGGER.warning("Running server with debug mode. NOT SUITABLE FOR PRODUCTION!")

app = Starlette(debug=cfg.DEBUG, routes=routes)

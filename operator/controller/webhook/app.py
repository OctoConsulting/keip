import logging.config
from json import JSONDecodeError

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.status import HTTP_400_BAD_REQUEST

from webhook import config as cfg
from webhook.introute.sync import sync
from webhook.logconf import LOG_CONF

_LOGGER = logging.getLogger(__name__)


async def webhook(request: Request):
    # Request API at https://metacontroller.github.io/metacontroller/api/compositecontroller.html#sync-hook-request
    try:
        body = await request.json()
        response = sync(body['parent'])
    except JSONDecodeError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Failed to parse request body')
    except KeyError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST,
                            detail=f'Missing field from request: {repr(e)}')
    return JSONResponse(response)


async def status(request):
    return JSONResponse({'status': 'UP'})


routes = [
    Route('/sync', endpoint=webhook, methods=['POST']),
    Route('/status', endpoint=status, methods=['GET']),
]

logging.config.dictConfig(LOG_CONF)

if cfg.DEBUG:
    _LOGGER.warning('Running server with debug mode. NOT SUITABLE FOR PRODUCTION!')

app = Starlette(debug=cfg.DEBUG, routes=routes)

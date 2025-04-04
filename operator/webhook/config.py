import logging
from starlette.config import Config

logging.captureWarnings(True)

env_file = ".env"
cfg = Config(env_file)

# Server
DEBUG = cfg("DEBUG", cast=bool, default=False)

# Application
INTEGRATION_CONTAINER_IMAGE = cfg(
    "INTEGRATION_IMAGE", cast=str, default="keip-integration"
)

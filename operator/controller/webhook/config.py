from starlette.config import Config

cfg = Config(".env")

# Server
DEBUG = cfg("DEBUG", cast=bool, default=False)

# Application
INTEGRATION_CONTAINER_IMAGE = cfg(
    "INTEGRATION_IMAGE", cast=str, default="ghcr.io/octoconsulting/keip-integration"
)

import logging
import os


def get_log_level_from_env():
    level = os.getenv("LOG_LEVEL", "").upper()
    if level in logging.getLevelNamesMapping().keys():
        return level
    return "INFO"


LOG_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        }
    },
    "root": {"handlers": ["stdout"], "level": get_log_level_from_env()},
}

import logging
import logging.config
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_FILE),
            "formatter": "default",
            "level": "INFO",
        },
        "console": {"class": "logging.StreamHandler", "formatter": "default", "level": "DEBUG"},
    },
    "root": {"handlers": ["file", "console"], "level": "INFO"},
}

def setup_logging():
    logging.config.dictConfig(LOGGING)

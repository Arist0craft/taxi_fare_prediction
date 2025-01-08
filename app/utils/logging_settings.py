import logging
import logging.config

from settings import get_settings

settings = get_settings()


def setup_logging():
    settings.LOGS_DIR.mkdir(exist_ok=True)
    logging.config.fileConfig(settings.LOGGING_CONFIG_PATH)

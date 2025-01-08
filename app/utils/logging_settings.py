import logging
import logging.config

import yaml
from settings import get_settings

settings = get_settings()


def setup_logging():
    settings.LOGS_DIR.mkdir(exist_ok=True)

    with settings.LOGGING_CONFIG_PATH.open(mode="r") as file:
        loaded_config = yaml.safe_load(file)
        logging.config.dictConfig(loaded_config)

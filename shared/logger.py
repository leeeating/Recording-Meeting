import logging
import logging.config
import yaml
from pathlib import Path
from .config import config


class EmailFilter(logging.Filter):
    def filter(self, record):
        return getattr(record, "send_email", False)


def setup_logger():
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    curr_folder = Path(__file__).parent
    config_path = curr_folder / "log_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        logging_dict = yaml.safe_load(f)

    logging_dict["root"]["level"] = config.LOG_LEVEL

    if "email" in logging_dict["handlers"]:
        email_h = logging_dict["handlers"]["email"]
        email_h["fromaddr"] = config.EMAIL_USER
        email_h["toaddrs"] = [config.EMAIL_USER]
        email_h["credentials"] = [config.EMAIL_USER, config.EMAIL_APP_PASSWORD]

    logging.config.dictConfig(logging_dict)

import yaml
import atexit
import queue
import logging
import logging.config
from logging import handlers
from pathlib import Path
from .config import config


class EmailFilter(logging.Filter):
    def filter(self, record):
        return getattr(record, "send_email", False)


class AsyncSMTPHandler(handlers.QueueHandler):
    def __init__(self, **kwargs):
        # 這些 key 會對應到你在 YAML 裡寫的欄位
        smtp_kwargs = {
            "mailhost": kwargs.pop("mailhost"),
            "fromaddr": kwargs.pop("fromaddr"),
            "toaddrs": kwargs.pop("toaddrs"),
            "subject": kwargs.pop("subject"),
            "credentials": kwargs.pop("credentials", None),
            "secure": kwargs.pop("secure", None),
            "timeout": kwargs.pop("timeout", 5.0),
        }

        self.internal_handler = handlers.SMTPHandler(**smtp_kwargs)

        self.log_queue = queue.Queue(-1)
        super().__init__(self.log_queue)

        self.listener = handlers.QueueListener(self.log_queue, self.internal_handler)
        self.listener.start()

        atexit.register(self.listener.stop)


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


if __name__ == "__main__":
    import time

    setup_logger()

    logger_app = logging.getLogger("app")
    logger_front = logging.getLogger("frontend")
    logger_root = logging.getLogger()

    print("=== 開始分流測試 ===")

    logger_app.info("這是後端的資訊內容")
    logger_app.error("這是後端的一般錯誤", extra={"send_email": False})

    # second : [4.39]
    t1 = time.time()
    logger_app.error("這是後端的【緊急】錯誤", extra={"send_email": True})
    print(time.time() - t1)

    logger_front.info("這是前端的界面資訊")

    # second : [3.53]
    t2 = time.time()
    logger_front.critical("前端崩潰了！發送郵件", extra={"send_email": True})
    print(time.time() - t2)

    logger_root.warning("這是一條 Root 的警告訊息")
    logger_root.info("這條 INFO 不會出現，因為 Root 設定為 WARNING")

    print("=== 測試指令已發送，請檢查結果 ===")

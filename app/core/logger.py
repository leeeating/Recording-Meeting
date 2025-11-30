import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "app.log"

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# File handler that rotates logs daily
file_handler = TimedRotatingFileHandler(
    filename=log_file,
    when="D",
    interval=1,
    backupCount=30,
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream handler for console output
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
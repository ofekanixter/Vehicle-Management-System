import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"


def setup_logging(level: int = logging.INFO) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"), maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(fmt)

    root.addHandler(console)
    root.addHandler(file_handler)

    logging.getLogger("pika").setLevel(logging.WARNING)

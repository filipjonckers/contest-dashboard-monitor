import logging
import sys

LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d %(levelname)s "
    "%(funcName)s:%(lineno)d > %(message)s"
)

LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

'''
Setup the logging configuration for this application.
'''


def setup_logging(level: int = logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    # Avoid adding handlers multiple times if this is called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

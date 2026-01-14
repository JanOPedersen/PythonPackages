import logging
from logging import Logger

def get_logger(
    name: str = "pipeline",
    level: int = logging.INFO,
) -> Logger:
    """
    Returns a configured logger with a consistent format.
    Ensures no duplicate handlers are added on repeated imports.
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if imported multiple times
    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    return logger

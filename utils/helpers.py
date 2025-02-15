from datetime import datetime
import logging
from typing import Any

def serialize_datetime(obj: Any) -> str:
    """Serialize a datetime object to ISO 8601 format.

    Args:
        obj (Any): The object to serialize.

    Returns:
        str: The serialized datetime string in ISO 8601 format.

    Raises:
        TypeError: If the object is not a datetime instance.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj).__name__} not serializable")


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger with a specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(name)

from datetime import datetime
from typing import Any, List
import logging

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
def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:

    """Split text into chunks with overlap."""
    # Find natural break points (paragraphs)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0

    for paragraph in paragraphs:
        paragraph_size = len(paragraph)

        if current_size + paragraph_size > chunk_size:
            # Store current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(chunk_text)

            # Start new chunk with overlap from previous
            if current_chunk and overlap > 0:
                overlap_text = current_chunk[-1]
                current_chunk = [overlap_text, paragraph]
                current_size = len(overlap_text) + paragraph_size
            else:
                current_chunk = [paragraph]
                current_size = paragraph_size
        else:
            current_chunk.append(paragraph)
            current_size += paragraph_size

    # Add the last chunk if there's anything left
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks
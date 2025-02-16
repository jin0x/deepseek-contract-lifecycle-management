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


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 500) -> List[dict]:
    """Split text into overlapping chunks while preserving structural integrity.

    Args:
        text (str): The text to be chunked
        chunk_size (int): Maximum size of each chunk (default: 4000 characters)
        overlap (int): Number of characters to overlap between chunks (default: 500)

    Returns:
        List[dict]: List of chunk dictionaries containing:
            - text: The chunk text
            - start_idx: Starting index in original text
            - end_idx: Ending index in original text
            - sequence: Chunk sequence number
    """
    # Find natural break points (paragraphs)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_count = 0
    start_idx = 0

    for paragraph in paragraphs:
        paragraph_size = len(paragraph)

        # If adding this paragraph exceeds chunk size
        if current_size + paragraph_size > chunk_size and current_chunk:
            # Store current chunk
            chunk_text = '\n\n'.join(current_chunk)
            end_idx = start_idx + len(chunk_text)
            chunks.append({
                'text': chunk_text,
                'start_idx': start_idx,
                'end_idx': end_idx,
                'sequence': chunk_count
            })

            # Start new chunk with overlap
            # Find the last complete paragraph that fits within overlap size
            overlap_size = 0
            overlap_paragraphs = []
            for p in reversed(current_chunk):
                if overlap_size + len(p) <= overlap:
                    overlap_paragraphs.insert(0, p)
                    overlap_size += len(p)
                else:
                    break

            # Start new chunk with overlap paragraphs
            current_chunk = overlap_paragraphs + [paragraph]
            current_size = sum(len(p) for p in current_chunk)
            start_idx = end_idx - overlap_size
            chunk_count += 1
        else:
            current_chunk.append(paragraph)
            current_size += paragraph_size

    # Add the last chunk if there's anything left
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append({
            'text': chunk_text,
            'start_idx': start_idx,
            'end_idx': start_idx + len(chunk_text),
            'sequence': chunk_count
        })

    return chunks
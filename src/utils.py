"""Utility functions for file hashing."""

import hashlib
from pathlib import Path
from typing import Union

from src.logger import get_logger


def hash_file(file_path: Union[str, Path], chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read (default 64KB)
        
    Returns:
        Hexadecimal SHA256 hash string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    logger = get_logger()
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        
        file_hash = hasher.hexdigest()
        logger.debug(f"Computed hash for {file_path.name}: {file_hash[:12]}...")
        
        return file_hash
        
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise


def hash_string(text: str) -> str:
    """Compute SHA256 hash of a string.
    
    Args:
        text: String to hash
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

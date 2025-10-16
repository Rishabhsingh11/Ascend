"""Cleanup utilities for logs and exports."""

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.logger import get_logger

load_dotenv()
logger = get_logger()


def cleanup_old_logs(logs_dir: str = "logs", max_age_hours: int = 24) -> int:
    """
    Delete log files older than specified hours.
    
    Args:
        logs_dir: Directory containing log files
        max_age_hours: Maximum age in hours (default: 24)
        
    Returns:
        Number of files deleted
    """
    logs_path = Path(logs_dir)
    
    if not logs_path.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    deleted_count = 0
    
    for log_file in logs_path.glob("*.log"):
        try:
            # Get file modification time
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_time < cutoff_time:
                log_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted old log: {log_file.name}")
        
        except Exception as e:
            logger.error(f"Failed to delete {log_file.name}: {e}")
    
    return deleted_count


def cleanup_exports_after_email(
    exports_dir: str = "exports",
    keep_latest: int = 5
) -> int:
    """
    Delete old export CSV files, keeping only the most recent ones.
    
    Args:
        exports_dir: Directory containing export files
        keep_latest: Number of most recent files to keep
        
    Returns:
        Number of files deleted
    """
    exports_path = Path(exports_dir)
    
    if not exports_path.exists():
        return 0
    
    # Get all CSV files sorted by modification time (newest first)
    csv_files = sorted(
        exports_path.glob("Jobs_*.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    # Keep only the latest N files
    files_to_delete = csv_files[keep_latest:]
    deleted_count = 0
    
    for csv_file in files_to_delete:
        try:
            csv_file.unlink()
            deleted_count += 1
            logger.info(f"Deleted old export: {csv_file.name}")
        except Exception as e:
            logger.error(f"Failed to delete {csv_file.name}: {e}")
    
    return deleted_count


def get_directory_size(directory: str) -> float:
    """
    Calculate total size of directory in MB.
    
    Args:
        directory: Path to directory
        
    Returns:
        Size in MB
    """
    total_size = 0
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return 0.0
    
    for file in dir_path.rglob("*"):
        if file.is_file():
            total_size += file.stat().st_size
    
    return total_size / (1024 * 1024)  # Convert to MB


def cleanup_all(
    logs_max_age: int = 24,
    exports_keep: int = 5
) -> dict:
    """
    Run all cleanup tasks.
    
    Args:
        logs_max_age: Max age for logs in hours
        exports_keep: Number of exports to keep
        
    Returns:
        Dictionary with cleanup results
    """
    results = {
        'logs_deleted': cleanup_old_logs(max_age_hours=logs_max_age),
        'exports_deleted': cleanup_exports_after_email(keep_latest=exports_keep),
        'logs_size_mb': get_directory_size('logs'),
        'exports_size_mb': get_directory_size('exports')
    }
    
    logger.info(f"Cleanup complete: {results}")
    
    return results

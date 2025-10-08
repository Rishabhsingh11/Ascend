"""Centralized logging system for the Job Search Agent."""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format the message
        formatted = super().format(record)
        
        # Add color to level name
        formatted = formatted.replace(
            record.levelname,
            f"{log_color}{record.levelname}{reset}"
        )
        
        return formatted


class AgentLogger:
    """Custom logger for the Job Search Agent with timing capabilities."""
    
    def __init__(self, name: str = "JobSearchAgent", log_file: Optional[str] = None):
        """Initialize the logger.
        
        Args:
            name: Logger name
            log_file: Optional log file path
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Clear existing handlers
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Generate log filename with timestamp if not provided
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"agent_run_{timestamp}.log"
        
        # Console handler - ONLY for debug/background info
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)  # Set to DEBUG to capture everything
        console_format = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # File handler with detailed format
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.log_file = log_file
        self.timers = {}
        
        self.debug(f"Logging initialized. Log file: {log_file}")
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message."""
        self.logger.critical(message)
    
    def start_timer(self, operation: str):
        """Start a timer for an operation.
        
        Args:
            operation: Name of the operation
        """
        self.timers[operation] = time.time()
        self.debug(f"Started: {operation}")
    
    def stop_timer(self, operation: str, success: bool = True):
        """Stop a timer and log the duration.
        
        Args:
            operation: Name of the operation
            success: Whether the operation succeeded
        """
        if operation not in self.timers:
            self.warning(f"Timer '{operation}' was never started")
            return
        
        elapsed = time.time() - self.timers[operation]
        status = "Completed" if success else "Failed"
        self.info(f"{status}: {operation} (Duration: {elapsed:.2f}s)")
        
        del self.timers[operation]
        return elapsed
    
    @contextmanager
    def timer(self, operation: str):
        """Context manager for timing operations.
        
        Args:
            operation: Name of the operation
            
        Example:
            with logger.timer("Download file"):
                download_file()
        """
        self.start_timer(operation)
        try:
            yield
            self.stop_timer(operation, success=True)
        except Exception as e:
            self.stop_timer(operation, success=False)
            self.error(f"Error in {operation}: {str(e)}")
            raise
    
    def log_separator(self, char: str = "=", length: int = 80):
        """Log a separator line.
        
        Args:
            char: Character to use for separator
            length: Length of separator line
        """
        self.info(char * length)
    
    def log_section(self, title: str):
        """Log a section header.
        
        Args:
            title: Section title
        """
        self.log_separator()
        self.info(f"  {title}")
        self.log_separator()


# Global logger instance
_global_logger: Optional[AgentLogger] = None


def get_logger() -> AgentLogger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AgentLogger()
    return _global_logger


def set_logger(logger: AgentLogger):
    """Set the global logger instance."""
    global _global_logger
    _global_logger = logger

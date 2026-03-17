"""
Configuration and logging setup for SQL Lineage project.

This module provides centralized configuration and logging utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


# ======================== Configuration ========================

class Config:
    """Application configuration constants."""
    
    # Server settings
    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 8001
    
    # File settings
    DEFAULT_OUTPUT_FILE: str = "lineage.json"
    SQL_FILE_EXTENSION: str = ".sql"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Frontend settings
    FRONTEND_DIR: str = "frontend"
    STATIC_DIR: str = "static"


# ======================== Logging Setup ========================

class LoggerSetup:
    """Centralized logging configuration."""
    
    _loggers: dict = {}
    
    @classmethod
    def get_logger(cls, name: str, level: str = Config.LOG_LEVEL) -> logging.Logger:
        """
        Get or create a logger with the given name.
        
        Args:
            name: Logger name (typically __name__)
            level: Logging level (default: INFO)
            
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level))
        
        # Only add handler if not present
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(getattr(logging, level))
            
            formatter = logging.Formatter(Config.LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        cls._loggers[name] = logger
        return logger


# ======================== Exception Classes ========================

class LineageException(Exception):
    """Base exception for lineage extraction."""
    pass


class SqlParsingError(LineageException):
    """Raised when SQL parsing fails."""
    pass


class FileProcessError(LineageException):
    """Raised when file processing fails."""
    pass


class ConfigError(LineageException):
    """Raised when configuration is invalid."""
    pass


class GraphBuildError(LineageException):
    """Raised when graph building fails."""
    pass

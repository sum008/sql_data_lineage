"""
File system scanning and SQL file discovery.

This module provides utilities for finding and reading SQL files
from the file system.
"""

import os
from pathlib import Path
from typing import List

from lineage.config import LoggerSetup, FileProcessError, Config


logger = LoggerSetup.get_logger(__name__)


class SqlFileScanner:
    """Scans directories for SQL files."""
    
    def __init__(self, extension: str = Config.SQL_FILE_EXTENSION):
        """
        Initialize the SQL file scanner.
        
        Args:
            extension: File extension to search for (default: .sql)
        """
        self.extension = extension
        self.logger = LoggerSetup.get_logger(__name__)
    
    def find_sql_files(self, folder: str) -> List[Path]:
        """
        Recursively find all SQL files in a directory.
        
        Args:
            folder: Directory path to search
            
        Returns:
            List of Path objects for SQL files found
            
        Raises:
            FileProcessError: If directory doesn't exist or is not readable
        """
        folder_path = Path(folder)
        
        if not folder_path.exists():
            raise FileProcessError(f"Folder does not exist: {folder}")
        
        if not folder_path.is_dir():
            raise FileProcessError(f"Path is not a directory: {folder}")
        
        sql_files: List[Path] = []
        
        try:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(self.extension):
                        file_path = Path(root) / file
                        sql_files.append(file_path)
                        self.logger.debug(f"Found SQL file: {file_path}")
        except PermissionError as e:
            raise FileProcessError(f"Permission denied while scanning directory: {str(e)}")
        except Exception as e:
            raise FileProcessError(f"Error scanning directory: {str(e)}")
        
        self.logger.info(f"Found {len(sql_files)} SQL file(s) in {folder}")
        return sorted(sql_files)


class SqlFileReader:
    """Reads SQL file contents."""
    
    def __init__(self, encoding: str = "utf-8"):
        """
        Initialize the SQL file reader.
        
        Args:
            encoding: File encoding (default: utf-8)
        """
        self.encoding = encoding
        self.logger = LoggerSetup.get_logger(__name__)
    
    def read_sql_file(self, file_path: Path) -> str:
        """
        Read and return the contents of a SQL file.
        
        Args:
            file_path: Path to the SQL file
            
        Returns:
            File contents as string
            
        Raises:
            FileProcessError: If file cannot be read
        """
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileProcessError(f"File does not exist: {file_path}")
            
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()
            
            self.logger.debug(f"Read SQL file: {file_path} ({len(content)} bytes)")
            return content
            
        except FileProcessError:
            raise
        except UnicodeDecodeError as e:
            raise FileProcessError(
                f"Failed to decode file (wrong encoding?): {file_path}\n{str(e)}"
            )
        except Exception as e:
            raise FileProcessError(f"Failed to read file {file_path}: {str(e)}")


# ======================== Convenience functions ========================

def find_sql_files(folder: str) -> List[Path]:
    """
    Find all SQL files in a folder (convenience function).
    
    Args:
        folder: Directory path to search
        
    Returns:
        List of Path objects
    """
    scanner = SqlFileScanner()
    return scanner.find_sql_files(folder)


def read_sql_file(file_path: Path) -> str:
    """
    Read SQL file contents (convenience function).
    
    Args:
        file_path: Path to the SQL file
        
    Returns:
        File contents as string
    """
    reader = SqlFileReader()
    return reader.read_sql_file(file_path)
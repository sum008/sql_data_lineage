"""
Command-line interface and batch processing logic.

This module handles scanning SQL files and processing lineage extraction
in batch mode for multiple files.
"""

import json
from pathlib import Path
from typing import List, Optional

from lineage.scanner import SqlFileScanner, SqlFileReader
from lineage.extractor import SqlLineageExtractor
from lineage.models import FileLineageResult
from lineage.config import LoggerSetup, FileProcessError


logger = LoggerSetup.get_logger(__name__)


class LineageScanProcessor:
    """Processes SQL files and extracts lineage in batch mode."""
    
    def __init__(self):
        """Initialize the scan processor."""
        self.logger = LoggerSetup.get_logger(__name__)
        self.file_scanner = SqlFileScanner()
        self.file_reader = SqlFileReader()
        self.lineage_extractor = SqlLineageExtractor()
    
    def process_folder(
        self,
        input_folder: str,
        output_file: str,
        target_table: Optional[str] = None
    ) -> None:
        """
        Scan a folder for SQL files and extract lineage from all of them.
        
        Args:
            input_folder: Path to folder containing SQL files
            output_file: Path to output JSON file
            target_table: Optional filter for specific table
            
        Raises:
            FileProcessError: If processing fails
        """
        try:
            # Find all SQL files
            self.logger.info(f"Scanning folder: {input_folder}")
            sql_files = self.file_scanner.find_sql_files(input_folder)
            
            if not sql_files:
                self.logger.warning(f"No SQL files found in {input_folder}")
            
            # Process each file
            results: List[FileLineageResult] = []
            
            for file in sql_files:
                result = self._process_file(file, target_table)
                results.append(result)
            
            # Write results to output file
            self._write_results(results, output_file)
            
            # Log summary
            successful = sum(1 for r in results if r.error is None)
            failed = len(results) - successful
            
            self.logger.info(
                f"Processed {len(sql_files)} SQL files: "
                f"{successful} successful, {failed} failed"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process folder: {str(e)}")
            raise
    
    def _process_file(
        self,
        file_path: Path,
        target_table: Optional[str] = None
    ) -> FileLineageResult:
        """
        Process a single SQL file and extract lineage.
        
        Args:
            file_path: Path to SQL file
            target_table: Optional filter for specific table
            
        Returns:
            FileLineageResult with either lineage or error
        """
        result = FileLineageResult(file_path=str(file_path))
        
        try:
            # Read SQL content
            sql_content = self.file_reader.read_sql_file(file_path)
            
            # Extract lineage
            lineage_records = self.lineage_extractor.extract_lineage_from_script(
                sql_content,
                target_table
            )
            
            result.lineage = lineage_records
            
            self.logger.debug(
                f"Processed {file_path}: {len(lineage_records)} lineage record(s)"
            )
            
        except Exception as e:
            result.error = str(e)
            self.logger.error(f"Error processing {file_path}: {str(e)}")
        
        return result
    
    def _write_results(self, results: List[FileLineageResult], output_file: str) -> None:
        """
        Write results to output JSON file.
        
        Args:
            results: List of FileLineageResult objects
            output_file: Path to output file
            
        Raises:
            FileProcessError: If writing fails
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert results to JSON-serializable format
            json_results = [
                {
                    "file": r.file_path,
                    "lineage": [l.to_dict() for l in r.lineage] if r.lineage else None,
                    "error": r.error,
                }
                for r in results
            ]
            
            with open(output_path, "w") as f:
                json.dump(json_results, f, indent=2)
            
            self.logger.info(f"Output written to {output_file}")
            
        except Exception as e:
            raise FileProcessError(f"Failed to write output file: {str(e)}")


# ======================== Module-level convenience function ========================

def run_scan(
    input_folder: str,
    output_file: str,
    target_table: Optional[str] = None
) -> None:
    """
    Run lineage extraction scan on a folder (CLI convenience function).
    
    Args:
        input_folder: Path to SQL files folder
        output_file: Path to output JSON file
        target_table: Optional table filter
    """
    processor = LineageScanProcessor()
    processor.process_folder(input_folder, output_file, target_table)
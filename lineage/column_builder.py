"""
Column-level lineage mapping from parsed lineage data.

This module builds mappings of table columns to their source columns,
enabling column-level data lineage tracking.
"""

import json
from pathlib import Path
from typing import Dict, List

from lineage.config import LoggerSetup, FileProcessError, GraphBuildError


logger = LoggerSetup.get_logger(__name__)


class ColumnLineageBuilder:
    """Builds column-level lineage mappings from lineage data."""
    
    def __init__(self):
        """Initialize the column lineage builder."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def build_column_lineage_from_json(self, json_file_path: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Build column lineage mappings from a lineage JSON file.
        
        Args:
            json_file_path: Path to lineage.json file
            
        Returns:
            Dictionary mapping table names to column mappings
            Each column mapping is {target_column: [source_columns]}
            
        Raises:
            FileProcessError: If file cannot be read
            GraphBuildError: If JSON is invalid
        """
        try:
            file_path = Path(json_file_path)
            
            if not file_path.exists():
                raise FileProcessError(f"File not found: {json_file_path}")
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded column lineage data from {json_file_path}")
            
        except FileProcessError:
            raise
        except json.JSONDecodeError as e:
            raise GraphBuildError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            raise FileProcessError(f"Failed to read JSON file: {str(e)}")
        
        return self._extract_column_lineage(data)
    
    def _extract_column_lineage(self, data: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
        """
        Extract column lineage mappings from loaded JSON data.
        
        Args:
            data: List of file entries from lineage JSON
            
        Returns:
            Column lineage mappings
        """
        column_lineage: Dict[str, Dict[str, List[str]]] = {}
        
        for entry in data:
            # Skip entries with errors
            if "error" in entry and entry["error"] is not None:
                self.logger.warning(
                    f"Skipping {entry.get('file', 'unknown')}: {entry['error']}"
                )
                continue
            
            lineage_records = entry.get("lineage", [])
            
            # Handle single record (dict) vs multiple records (list)
            if isinstance(lineage_records, dict):
                lineage_records = [lineage_records]
            
            # Process each lineage record
            for record in lineage_records:
                try:
                    self._process_lineage_record(record, column_lineage)
                except Exception as e:
                    self.logger.warning(f"Failed to process lineage record: {str(e)}")
                    continue
        
        self.logger.debug(
            f"Built column lineage for {len(column_lineage)} table(s)"
        )
        
        return column_lineage
    
    @staticmethod
    def _process_lineage_record(
        record: Dict,
        column_lineage: Dict[str, Dict[str, List[str]]]
    ) -> None:
        """
        Process a single lineage record and update column lineage mapping.
        
        Args:
            record: Lineage record dictionary
            column_lineage: Dictionary to update with column mappings
        """
        target_table = record.get("target_table")
        
        if not target_table:
            return
        
        # Initialize table entry if not present
        if target_table not in column_lineage:
            column_lineage[target_table] = {}
        
        # Process each column's lineage
        for column_info in record.get("column_lineage", []):
            target_column = column_info.get("target_column")
            source_columns = column_info.get("source_columns", [])
            
            if target_column:
                column_lineage[target_table][target_column] = source_columns


# ======================== Convenience functions ========================

def build_column_lineage(lineage_json_path: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Build column lineage from lineage JSON file (convenience function).
    
    Args:
        lineage_json_path: Path to lineage.json file
        
    Returns:
        Dictionary mapping tables to column lineage
    """
    builder = ColumnLineageBuilder()
    return builder.build_column_lineage_from_json(lineage_json_path)
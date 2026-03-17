"""
SQL statement parsing and lineage extraction.

This module provides classes for parsing SQL statements and extracting
table and column-level lineage information.
"""

from typing import Dict, List, Optional, Set
import sqlglot
from sqlglot import exp

from lineage.models import ColumnInfo, LineageRecord
from lineage.config import LoggerSetup, SqlParsingError


logger = LoggerSetup.get_logger(__name__)


class TableExtractor:
    """Extracts table-level lineage from SQL statements."""
    
    def __init__(self):
        """Initialize the table extractor."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def extract_target_table(self, parsed: exp.Expression) -> Optional[str]:
        """
        Extract target table from parsed SQL expression.
        
        Supports: INSERT, CREATE, UPDATE, DELETE, MERGE statements.
        
        Args:
            parsed: Parsed SQL expression
            
        Returns:
            Normalized table name or None
        """
        target_table = None
        
        if isinstance(parsed, exp.Insert):
            target_table = parsed.this.name
        elif isinstance(parsed, exp.Create):
            target_table = parsed.this.name
        elif isinstance(parsed, exp.Update):
            target_table = parsed.this.name
        elif isinstance(parsed, exp.Delete):
            target_table = parsed.this.name
        elif isinstance(parsed, exp.Merge):
            target_table = parsed.this.name
        
        return self.normalize_table_name(target_table) if target_table else None
    
    def extract_source_tables(self, parsed: exp.Expression) -> Set[str]:
        """
        Extract all source tables from parsed SQL expression.
        
        Args:
            parsed: Parsed SQL expression
            
        Returns:
            Set of normalized source table names
        """
        source_tables: Set[str] = set()
        
        for table in parsed.find_all(exp.Table):
            normalized = self.normalize_table_name(table.name)
            if normalized:
                source_tables.add(normalized)
        
        return source_tables
    
    def extract_cte_sources(self, parsed: exp.Expression) -> Set[str]:
        """
        Extract all Common Table Expressions (CTEs) from parsed SQL expression.
        
        Args:
            parsed: Parsed SQL expression
            
        Returns:
            Set of CTE aliases
        """
        cte_sources: Set[str] = set()
        
        for cte in parsed.find_all(exp.CTE):
            if cte.alias:
                cte_sources.add(cte.alias)
        
        return cte_sources
    
    @staticmethod
    def normalize_table_name(name: Optional[str]) -> Optional[str]:
        """
        Normalize table name by extracting the last component and lowercasing.
        
        Handles schema.table format by extracting only the table name.
        
        Args:
            name: Table name (may include schema)
            
        Returns:
            Normalized table name in lowercase
        """
        if not name:
            return None
        
        return name.split(".")[-1].lower()


class ColumnExtractor:
    """Extracts column-level lineage from SQL SELECT statements."""
    
    def __init__(self):
        """Initialize the column extractor."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def extract_column_lineage(
        self, 
        select: Optional[exp.Select],
        alias_map: Dict[str, str]
    ) -> List[ColumnInfo]:
        """
        Extract column-level lineage from SELECT statement.
        
        Maps output columns to their source columns through transformations.
        
        Args:
            select: SELECT expression (can be None)
            alias_map: Mapping of table aliases to table names
            
        Returns:
            List of ColumnInfo objects
        """
        column_lineage: List[ColumnInfo] = []
        
        if not select:
            return column_lineage
        
        for projection in select.expressions:
            if isinstance(projection, exp.Alias):
                column_lineage.append(self._extract_aliased_column(projection, alias_map))
            elif isinstance(projection, exp.Column):
                column_lineage.append(self._extract_simple_column(projection, alias_map))
        
        return column_lineage
    
    def _extract_aliased_column(
        self, 
        projection: exp.Alias, 
        alias_map: Dict[str, str]
    ) -> ColumnInfo:
        """
        Extract column lineage from an aliased projection.
        
        Args:
            projection: Aliased expression
            alias_map: Table alias mapping
            
        Returns:
            ColumnInfo with target and source columns
        """
        target_column = projection.alias
        source_columns: List[str] = []
        
        for col in projection.find_all(exp.Column):
            source_col = self._format_column_reference(col, alias_map)
            if source_col:
                source_columns.append(source_col)
        
        return ColumnInfo(target_column=target_column, source_columns=source_columns)
    
    def _extract_simple_column(
        self, 
        projection: exp.Column, 
        alias_map: Dict[str, str]
    ) -> ColumnInfo:
        """
        Extract column lineage from a simple column projection.
        
        Args:
            projection: Column expression
            alias_map: Table alias mapping
            
        Returns:
            ColumnInfo object
        """
        target_column = projection.name
        source_col = self._format_column_reference(projection, alias_map)
        
        return ColumnInfo(
            target_column=target_column,
            source_columns=[source_col] if source_col else []
        )
    
    @staticmethod
    def _format_column_reference(
        col: exp.Column, 
        alias_map: Dict[str, str]
    ) -> Optional[str]:
        """
        Format a column reference with table prefix if available.
        
        Args:
            col: Column expression
            alias_map: Table alias mapping
            
        Returns:
            Formatted column reference (e.g., "table.column" or "column")
        """
        if col.table:
            table_name = alias_map.get(col.table, col.table)
            return f"{table_name}.{col.name}"
        
        return col.name


class SqlLineageExtractor:
    """Main class for extracting SQL lineage from SQL scripts."""
    
    def __init__(self):
        """Initialize the SQL lineage extractor."""
        self.logger = LoggerSetup.get_logger(__name__)
        self.table_extractor = TableExtractor()
        self.column_extractor = ColumnExtractor()
    
    def extract_lineage_from_script(
        self, 
        sql_script: str,
        target_table: Optional[str] = None
    ) -> List[LineageRecord]:
        """
        Extract lineage from a complete SQL script with multiple statements.
        
        Args:
            sql_script: SQL script content (may contain multiple statements)
            target_table: Optional filter to only extract lineage for this table
            
        Returns:
            List of LineageRecord objects
            
        Raises:
            SqlParsingError: If SQL parsing fails
        """
        results: List[LineageRecord] = []
        
        try:
            statements = sqlglot.parse(sql_script)
            self.logger.debug(f"Parsed {len(statements)} SQL statement(s)")
        except Exception as e:
            raise SqlParsingError(f"Failed to parse SQL script: {str(e)}")
        
        for stmt in statements:
            try:
                lineage = self.extract_lineage_from_statement(
                    stmt.sql(), 
                    target_table
                )
                if lineage:
                    results.append(lineage)
            except Exception as e:
                self.logger.warning(f"Failed to extract lineage from statement: {str(e)}")
                continue
        
        return results
    
    def extract_lineage_from_statement(
        self, 
        sql: str,
        target_table: Optional[str] = None
    ) -> Optional[LineageRecord]:
        """
        Extract lineage from a single SQL statement.
        
        Args:
            sql: Single SQL statement
            target_table: Optional filter to only extract lineage for this table
            
        Returns:
            LineageRecord or None if target_table filter doesn't match
            
        Raises:
            SqlParsingError: If SQL parsing fails
        """
        try:
            parsed = sqlglot.parse_one(sql)
        except Exception as e:
            raise SqlParsingError(f"Failed to parse SQL statement: {str(e)}")
        
        # Extract target table
        target = self.table_extractor.extract_target_table(parsed)
        
        # Apply target table filter if specified
        if target_table and target != target_table:
            return None
        
        # Extract source tables
        source_tables = self.table_extractor.extract_source_tables(parsed)
        
        # Extract CTEs
        cte_sources = self.table_extractor.extract_cte_sources(parsed)
        
        # Remove target table from sources if present
        if target in source_tables:
            source_tables.remove(target)
        
        # Remove CTEs from source tables
        source_tables = source_tables - cte_sources
        
        # Build alias map for column tracking
        alias_map = self._build_alias_map(parsed)
        
        # Extract column-level lineage
        select = parsed.find(exp.Select)
        column_lineage = self.column_extractor.extract_column_lineage(select, alias_map)
        
        # Create lineage record
        lineage_record = LineageRecord(
            target_table=target,
            source_tables=sorted(list(source_tables)),
            cte_sources=sorted(list(cte_sources)),
            column_lineage=column_lineage
        )
        
        self.logger.debug(
            f"Extracted lineage for {target}: "
            f"{len(source_tables)} sources, {len(column_lineage)} columns"
        )
        
        return lineage_record
    
    @staticmethod
    def _build_alias_map(parsed: exp.Expression) -> Dict[str, str]:
        """
        Build a mapping from table aliases to actual table names.
        
        Args:
            parsed: Parsed SQL expression
            
        Returns:
            Dictionary mapping aliases to table names
        """
        alias_map: Dict[str, str] = {}
        
        for table in parsed.find_all(exp.Table):
            if table.alias:
                alias_map[table.alias] = table.name
        
        return alias_map


# ======================== Module-level convenience functions ========================

def extract_lineage(sql_script: str, target_table: Optional[str] = None) -> List[Dict]:
    """
    Extract lineage from SQL script (module-level convenience function).
    
    Args:
        sql_script: SQL script content
        target_table: Optional filter to only extract lineage for this table
        
    Returns:
        List of lineage dictionaries
    """
    extractor = SqlLineageExtractor()
    records = extractor.extract_lineage_from_script(sql_script, target_table)
    return [record.to_dict() for record in records]
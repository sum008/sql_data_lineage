"""
SQL Data Lineage - A tool for extracting and visualizing SQL data lineage.

This package provides utilities for parsing SQL statements, extracting table and
column-level lineage information, building lineage graphs, and visualizing the
results through an interactive web interface.

Main modules:
    - extractor: SQL parsing and lineage extraction
    - scanner: File system scanning for SQL files
    - graph_builder: Building lineage graphs
    - column_builder: Column-level lineage extraction
    - search: Graph search and filtering
    - cli: Command-line interface and batch processing
    - viz: Web visualization server
    - models: Data models and structures
    - config: Configuration and logging setup

Quick Start:
    from lineage.extractor import extract_lineage
    
    sql = "CREATE TABLE target SELECT * FROM source"
    lineage = extract_lineage(sql)
    print(lineage)
"""

from lineage.extractor import (
    SqlLineageExtractor,
    TableExtractor,
    ColumnExtractor,
    extract_lineage,
)
from lineage.scanner import (
    SqlFileScanner,
    SqlFileReader,
    find_sql_files,
    read_sql_file,
)
from lineage.graph_builder import (
    GraphBuilder,
    build_graph,
)
from lineage.column_builder import (
    ColumnLineageBuilder,
    build_column_lineage,
)
from lineage.search import (
    GraphSearcher,
    get_upstream_lineage,
    get_downstream_lineage,
    get_full_lineage,
)
from lineage.cli import (
    LineageScanProcessor,
    run_scan,
)
from lineage.viz import (
    LineageVisualizationServer,
    run_viz,
)
from lineage.models import (
    ColumnInfo,
    LineageRecord,
    FileLineageResult,
    GraphNode,
    GraphEdge,
    Graph,
)
from lineage.config import (
    Config,
    LoggerSetup,
    LineageException,
    SqlParsingError,
    FileProcessError,
    ConfigError,
    GraphBuildError,
)

__version__ = "1.0.0"
__author__ = "SQL Data Lineage Team"

__all__ = [
    # Extractors
    "SqlLineageExtractor",
    "TableExtractor",
    "ColumnExtractor",
    "extract_lineage",
    # Scanners
    "SqlFileScanner",
    "SqlFileReader",
    "find_sql_files",
    "read_sql_file",
    # Graph Operations
    "GraphBuilder",
    "build_graph",
    "ColumnLineageBuilder",
    "build_column_lineage",
    # Search
    "GraphSearcher",
    "get_upstream_lineage",
    "get_downstream_lineage",
    "get_full_lineage",
    # CLI and Viz
    "LineageScanProcessor",
    "run_scan",
    "LineageVisualizationServer",
    "run_viz",
    # Models
    "ColumnInfo",
    "LineageRecord",
    "FileLineageResult",
    "GraphNode",
    "GraphEdge",
    "Graph",
    # Config
    "Config",
    "LoggerSetup",
    "LineageException",
    "SqlParsingError",
    "FileProcessError",
    "ConfigError",
    "GraphBuildError",
]

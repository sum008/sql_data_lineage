"""
Data models for SQL Lineage project.

This module defines Pydantic models and dataclasses for type safety
and data validation throughout the application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


# ======================== Data Classes ========================

@dataclass
class ColumnInfo:
    """Represents a column lineage mapping."""
    target_column: str
    source_columns: List[str] = field(default_factory=list)


@dataclass
class LineageRecord:
    """Represents the complete lineage for a single SQL statement."""
    target_table: Optional[str]
    source_tables: List[str]
    cte_sources: List[str]
    column_lineage: List[ColumnInfo] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "target_table": self.target_table,
            "source_tables": self.source_tables,
            "cte_sources": self.cte_sources,
            "column_lineage": [
                {
                    "target_column": col.target_column,
                    "source_columns": col.source_columns,
                }
                for col in self.column_lineage
            ],
        }


@dataclass
class FileLineageResult:
    """Result of parsing a single file."""
    file_path: str
    lineage: Optional[List[LineageRecord]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file_path,
            "lineage": [l.to_dict() for l in self.lineage] if self.lineage else None,
            "error": self.error,
        }


@dataclass
class GraphNode:
    """Represents a node in the lineage graph."""
    id: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {"id": self.id}


@dataclass
class GraphEdge:
    """Represents an edge in the lineage graph."""
    source: str
    target: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {"source": self.source, "target": self.target}


@dataclass
class Graph:
    """Represents the complete lineage graph."""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


# ======================== Pydantic Models (for API responses) ========================

class ColumnLineageResponse(BaseModel):
    """API response for column lineage."""
    pass  # Dynamic based on table


class GraphResponse(BaseModel):
    """API response for the graph."""
    nodes: List[Dict[str, str]] = Field(..., description="List of node objects with id")
    edges: List[Dict[str, str]] = Field(..., description="List of edge objects with source and target")


class UpstreamLineageResponse(BaseModel):
    """API response for upstream lineage search."""
    nodes: List[Dict[str, str]] = Field(..., description="Filtered nodes")
    edges: List[Dict[str, str]] = Field(..., description="Filtered edges")

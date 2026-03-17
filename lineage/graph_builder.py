"""
Lineage graph construction from parsed lineage data.

This module converts lineage records into a graph structure suitable
for visualization and analysis.
"""

import json
from pathlib import Path
from typing import Dict, List, Set

from lineage.models import Graph, GraphNode, GraphEdge, LineageRecord
from lineage.config import LoggerSetup, FileProcessError, GraphBuildError


logger = LoggerSetup.get_logger(__name__)


class GraphBuilder:
    """Builds a lineage graph from lineage records."""
    
    def __init__(self):
        """Initialize the graph builder."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def build_graph_from_records(self, lineage_records: List[LineageRecord]) -> Graph:
        """
        Build a graph from lineage records.
        
        Args:
            lineage_records: List of LineageRecord objects
            
        Returns:
            Graph object containing nodes and edges
        """
        nodes: Set[str] = set()
        edges: List[GraphEdge] = []
        target_to_sources = {}
        # Collect all nodes and edges from lineage records
        for record in lineage_records:
            if not record.target_table:
                self.logger.warning("Skipping record with no target table")
                continue
            
            nodes.add(record.target_table)
            
            for source in record.source_tables:
                nodes.add(source)
                target_to_sources.setdefault(record.target_table, set()).add(source)
        # Create edges from target_to_sources
        for target, sources in target_to_sources.items():
            for source in sources:
                edges.append(GraphEdge(source=source, target=target))
        
        # Create Graph object
        graph_nodes = [GraphNode(id=node_id) for node_id in sorted(nodes)]
        
        self.logger.debug(
            f"Built graph with {len(graph_nodes)} nodes and {len(edges)} edges"
        )
        
        return Graph(nodes=graph_nodes, edges=edges)
    
    def build_graph_from_json_file(self, json_file_path: str) -> Graph:
        """
        Build a graph from a lineage JSON file.
        
        Args:
            json_file_path: Path to lineage.json file
            
        Returns:
            Graph object
            
        Raises:
            FileProcessError: If file cannot be read
            GraphBuildError: If graph building fails
        """
        try:
            file_path = Path(json_file_path)
            
            if not file_path.exists():
                raise FileProcessError(f"File not found: {json_file_path}")
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded lineage data from {json_file_path}")
            
        except FileProcessError:
            raise
        except json.JSONDecodeError as e:
            raise GraphBuildError(f"Invalid JSON file: {str(e)}")
        except Exception as e:
            raise FileProcessError(f"Failed to read JSON file: {str(e)}")
        
        # Extract lineage records from data
        lineage_records: List[LineageRecord] = []
        
        for entry in data:
            if "error" in entry and entry["error"] is not None:
                self.logger.warning(
                    f"Skipping {entry.get('file', 'unknown')}: {entry['error']}"
                )
                continue
            
            lineage_list = entry.get("lineage", [])
            if isinstance(lineage_list, dict):
                lineage_list = [lineage_list]
            
            for record_dict in lineage_list:
                try:
                    record = self._dict_to_lineage_record(record_dict)
                    lineage_records.append(record)
                except Exception as e:
                    self.logger.warning(f"Failed to parse lineage record: {str(e)}")
                    continue
        
        return self.build_graph_from_records(lineage_records)
    
    @staticmethod
    def _dict_to_lineage_record(record_dict: Dict) -> LineageRecord:
        """
        Convert a dictionary to a LineageRecord object.
        
        Args:
            record_dict: Dictionary representation of a lineage record
            
        Returns:
            LineageRecord object
        """
        return LineageRecord(
            target_table=record_dict.get("target_table"),
            source_tables=record_dict.get("source_tables", []),
            cte_sources=record_dict.get("cte_sources", []),
            column_lineage=[]  # Column lineage handled separately
        )


# ======================== Convenience functions ========================

def build_graph(lineage_json_path: str) -> Dict:
    """
    Build a graph from lineage JSON file (convenience function).
    
    Args:
        lineage_json_path: Path to lineage.json file
        
    Returns:
        Dictionary representation of the graph
    """
    builder = GraphBuilder()
    graph = builder.build_graph_from_json_file(lineage_json_path)
    return graph.to_dict()


if __name__ == "__main__":
    res=build_graph("/Users/sumit/Documents/lineage.json")
    print(json.dumps(res, indent=2))
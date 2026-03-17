"""
Graph search and filtering for lineage exploration.

This module provides utilities for searching and filtering the lineage graph
to find upstream/downstream dependencies for specific tables.
"""

from typing import Dict, List, Set

from lineage.config import LoggerSetup


logger = LoggerSetup.get_logger(__name__)


class GraphSearcher:
    """Searches and filters the lineage graph."""
    
    def __init__(self):
        """Initialize the graph searcher."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def get_upstream_lineage(self, graph: Dict, search_table: str) -> Dict:
        """
        Find all upstream dependencies for a given table.
        
        Performs a depth-first search starting from the search table
        and traversing backwards through all source tables.
        
        Args:
            graph: Graph dictionary with 'nodes' and 'edges' keys
            search_table: Table name to search for
            
        Returns:
            Filtered graph containing only the upstream lineage
        """
        # Build indexes for efficient lookup
        target_to_sources, _ = self._build_graph_indexes(graph)
        
        # Find all upstream tables via DFS
        visited: Set[str] = set()
        self._dfs_upstream(search_table, target_to_sources, visited)
        
        # Filter graph to only include visited nodes/edges
        filtered_nodes = [
            node for node in graph.get("nodes", [])
            if node.get("id") in visited
        ]
        
        filtered_edges = [
            edge for edge in graph.get("edges", [])
            if edge.get("source") in visited and edge.get("target") in visited
        ]
        
        self.logger.debug(
            f"Found upstream lineage for {search_table}: "
            f"{len(visited)} tables, {len(filtered_edges)} relationships"
        )
        
        return {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
        }
    
    def get_downstream_lineage(self, graph: Dict, search_table: str) -> Dict:
        """
        Find all downstream dependencies for a given table.
        
        Performs a depth-first search starting from the search table
        and traversing forwards through all target tables.
        
        Args:
            graph: Graph dictionary with 'nodes' and 'edges' keys
            search_table: Table name to search for
            
        Returns:
            Filtered graph containing only the downstream lineage
        """
        # Build indexes for efficient lookup
        _, source_to_targets = self._build_graph_indexes(graph)
        
        # Find all downstream tables via DFS
        visited: Set[str] = set()
        self._dfs_downstream(search_table, source_to_targets, visited)
        
        # Filter graph to only include visited nodes/edges
        filtered_nodes = [
            node for node in graph.get("nodes", [])
            if node.get("id") in visited
        ]
        
        filtered_edges = [
            edge for edge in graph.get("edges", [])
            if edge.get("source") in visited and edge.get("target") in visited
        ]
        
        self.logger.debug(
            f"Found downstream lineage for {search_table}: "
            f"{len(visited)} tables, {len(filtered_edges)} relationships"
        )
        
        return {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
        }
    
    def get_full_lineage(self, graph: Dict, search_table: str) -> Dict:
        """
        Find both upstream and downstream dependencies for a given table.
        
        Args:
            graph: Graph dictionary with 'nodes' and 'edges' keys
            search_table: Table name to search for
            
        Returns:
            Filtered graph containing the complete lineage
        """
        target_to_sources, source_to_targets = self._build_graph_indexes(graph)
        
        # Find all related tables
        visited: Set[str] = {search_table}
        self._dfs_upstream(search_table, target_to_sources, visited)
        self._dfs_downstream(search_table, source_to_targets, visited)
        
        # Filter graph
        filtered_nodes = [
            node for node in graph.get("nodes", [])
            if node.get("id") in visited
        ]
        
        filtered_edges = [
            edge for edge in graph.get("edges", [])
            if edge.get("source") in visited and edge.get("target") in visited
        ]
        
        return {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
        }
    
    @staticmethod
    def _build_graph_indexes(graph: Dict) -> tuple:
        """
        Build efficient lookup indexes for the graph.
        
        Args:
            graph: Graph dictionary with 'edges' key
            
        Returns:
            Tuple of (target_to_sources, source_to_targets) dictionaries
        """
        target_to_sources: Dict[str, Set[str]] = {}
        source_to_targets: Dict[str, Set[str]] = {}
        
        for edge in graph.get("edges", []):
            src = edge.get("source")
            tgt = edge.get("target")
            
            if src and tgt:
                target_to_sources.setdefault(tgt, set()).add(src)
                source_to_targets.setdefault(src, set()).add(tgt)
        
        return target_to_sources, source_to_targets
    
    @staticmethod
    def _dfs_upstream(
        table: str,
        target_to_sources: Dict[str, Set[str]],
        visited: Set[str]
    ) -> None:
        """
        Depth-first search to find all upstream sources.
        
        Args:
            table: Starting table name
            target_to_sources: Map of targets to their sources
            visited: Set to accumulate visited tables
        """
        if table in visited:
            return
        
        visited.add(table)
        
        for source in target_to_sources.get(table, set()):
            GraphSearcher._dfs_upstream(source, target_to_sources, visited)
    
    @staticmethod
    def _dfs_downstream(
        table: str,
        source_to_targets: Dict[str, Set[str]],
        visited: Set[str]
    ) -> None:
        """
        Depth-first search to find all downstream targets.
        
        Args:
            table: Starting table name
            source_to_targets: Map of sources to their targets
            visited: Set to accumulate visited tables
        """
        if table in visited:
            return
        
        visited.add(table)
        
        for target in source_to_targets.get(table, set()):
            GraphSearcher._dfs_downstream(target, source_to_targets, visited)


# ======================== Convenience functions ========================

def get_upstream_lineage(graph: Dict, search_table: str) -> Dict:
    """
    Get upstream lineage (convenience function).
    
    Args:
        graph: Complete lineage graph
        search_table: Table to search for
        
    Returns:
        Filtered graph with upstream dependencies
    """
    searcher = GraphSearcher()
    return searcher.get_upstream_lineage(graph, search_table)


def get_downstream_lineage(graph: Dict, search_table: str) -> Dict:
    """
    Get downstream lineage (convenience function).
    
    Args:
        graph: Complete lineage graph
        search_table: Table to search for
        
    Returns:
        Filtered graph with downstream dependencies
    """
    searcher = GraphSearcher()
    return searcher.get_downstream_lineage(graph, search_table)


def get_full_lineage(graph: Dict, search_table: str) -> Dict:
    """
    Get complete lineage (convenience function).
    
    Args:
        graph: Complete lineage graph
        search_table: Table to search for
        
    Returns:
        Filtered graph with full lineage
    """
    searcher = GraphSearcher()
    return searcher.get_full_lineage(graph, search_table)
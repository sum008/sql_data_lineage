"""
Web visualization server for lineage graphs.

This module provides a FastAPI web server with REST API endpoints
for exploring lineage data through an interactive web interface.
"""

from typing import Dict, Optional, List
import json
import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from lineage.column_builder import ColumnLineageBuilder
from lineage.graph_builder import GraphBuilder
from lineage.search import GraphSearcher
from lineage.config import LoggerSetup, Config, FileProcessError, GraphBuildError


logger = LoggerSetup.get_logger(__name__)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Middleware to disable caching for development."""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


class LineageVisualizationServer:
    """FastAPI server for lineage visualization."""
    
    def __init__(self, lineage_json_path: str):
        """
        Initialize the visualization server.
        
        Args:
            lineage_json_path: Path to lineage.json file
            
        Raises:
            FileProcessError: If lineage file cannot be loaded
        """
        self.logger = LoggerSetup.get_logger(__name__)
        self.lineage_json_path = lineage_json_path
        
        # Build graph and column lineage
        try:
            self.logger.info(f"Loading lineage data from {lineage_json_path}")
            
            graph_builder = GraphBuilder()
            self.graph = graph_builder.build_graph_from_json_file(lineage_json_path)
            
            column_builder = ColumnLineageBuilder()
            self.column_lineage = column_builder.build_column_lineage_from_json(
                lineage_json_path
            )
            
            self.searcher = GraphSearcher()
            
            # Build table-to-columns mapping
            self._build_tables_columns_map()
            
            self.logger.info("Lineage data loaded successfully")
            
        except (FileProcessError, GraphBuildError) as e:
            self.logger.error(f"Failed to load lineage data: {str(e)}")
            raise
    
    def _build_tables_columns_map(self) -> None:
        """Build a mapping of tables to their columns from the lineage data."""
        self.tables_columns = {}
        
        try:
            # Load the raw JSON to extract column information
            with open(self.lineage_json_path, 'r') as f:
                data = json.load(f)
            
            # Extract all tables and their columns from column_lineage
            for file_entry in data:
                if file_entry.get('lineage'):
                    for lineage_item in file_entry['lineage']:
                        target_table = lineage_item.get('target_table')
                        if target_table:
                            if target_table not in self.tables_columns:
                                self.tables_columns[target_table] = set()
                            
                            # Add columns from column_lineage
                            for col_info in lineage_item.get('column_lineage', []):
                                target_col = col_info.get('target_column')
                                if target_col:
                                    self.tables_columns[target_table].add(target_col)
                        
                        # Also add source tables
                        for source_table in lineage_item.get('source_tables', []):
                            if source_table not in self.tables_columns:
                                self.tables_columns[source_table] = set()
            
            # Convert sets to sorted lists
            for table in self.tables_columns:
                self.tables_columns[table] = sorted(list(self.tables_columns[table]))
            
            self.logger.debug(f"Found {len(self.tables_columns)} tables")
            
        except Exception as e:
            self.logger.warning(f"Error building tables-columns map: {str(e)}")
            self.tables_columns = {}
    
    def create_app(self) -> FastAPI:
        """
        Create and configure the FastAPI application.
        
        Returns:
            FastAPI application instance
        """
        app = FastAPI(
            title="SQL Lineage Viewer",
            description="Interactive visualization of SQL data lineage",
            version="1.0.0"
        )
        
        # Add no-cache middleware
        app.add_middleware(NoCacheMiddleware)
        
        # Mount static files
        try:
            app.mount(
                f"/{Config.STATIC_DIR}",
                StaticFiles(directory=Config.FRONTEND_DIR),
                name=Config.STATIC_DIR
            )
        except RuntimeError as e:
            self.logger.warning(f"Could not mount static files: {str(e)}")
        
        # Define routes
        @app.get("/", tags=["Frontend"])
        def index() -> FileResponse:
            """Serve the main HTML interface."""
            return FileResponse(f"{Config.FRONTEND_DIR}/index.html")
        
        @app.get("/graph", tags=["API"])
        def get_graph() -> Dict:
            """
            Get the complete lineage graph.
            
            Returns:
                Graph with nodes and edges
            """
            self.logger.debug("Fetching complete graph")
            return self.graph.to_dict() if hasattr(self.graph, 'to_dict') else self.graph
        
        @app.get("/lineage/{table}", tags=["API"])
        def get_lineage(table: str) -> Dict:
            """
            Get upstream lineage for a specific table.
            
            Args:
                table: Table name to search for
                
            Returns:
                Filtered graph with upstream dependencies
                
            Raises:
                HTTPException: If table not found
            """
            self.logger.debug(f"Fetching lineage for table: {table}")
            
            graph_dict = self.graph.to_dict() if hasattr(self.graph, 'to_dict') else self.graph
            
            # Check if table exists in graph
            node_ids = {node.get("id") for node in graph_dict.get("nodes", [])}
            if table not in node_ids:
                self.logger.warning(f"Table not found: {table}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Table '{table}' not found in lineage"
                )
            
            return self.searcher.get_upstream_lineage(graph_dict, table)
        
        @app.get("/column-lineage/{table}", tags=["API"])
        def get_column_lineage(table: str) -> Dict[str, list]:
            """
            Get column-level lineage for a specific table.
            
            Args:
                table: Table name to retrieve column lineage for
                
            Returns:
                Mapping of target columns to source columns
            """
            self.logger.debug(f"Fetching column lineage for table: {table}")
            
            return self.column_lineage.get(table, {})
        
        @app.get("/tables", tags=["API"])
        def get_tables() -> Dict[str, List[str]]:
            """
            Get all tables found in the lineage data.
            
            Returns:
                List of all table names
            """
            self.logger.debug("Fetching all tables")
            tables = sorted(list(self.tables_columns.keys()))
            return {"tables": tables}
        
        @app.get("/tables/{table}/columns", tags=["API"])
        def get_table_columns(table: str) -> Dict[str, List[str]]:
            """
            Get all columns for a specific table.
            
            Args:
                table: Table name
                
            Returns:
                List of column names for the table
                
            Raises:
                HTTPException: If table not found
            """
            self.logger.debug(f"Fetching columns for table: {table}")
            
            if table not in self.tables_columns:
                self.logger.warning(f"Table not found: {table}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Table '{table}' not found"
                )
            
            return {"columns": self.tables_columns[table]}
        
        return app


def run_viz(
    lineage_json: str,
    host: str = Config.DEFAULT_HOST,
    port: int = Config.DEFAULT_PORT,
    reload: bool = False
) -> None:
    """
    Run the visualization server.
    
    Args:
        lineage_json: Path to lineage.json file
        host: Server host (default: 0.0.0.0)
        port: Server port (default: 8001)
        reload: Enable auto-reload on file changes
        
    Raises:
        FileProcessError: If lineage file cannot be loaded
    """
    try:
        # Create server
        server = LineageVisualizationServer(lineage_json)
        app = server.create_app()
        
        # Print startup message
        print(f"\n{'='*50}")
        print("Lineage UI running at:")
        print(f"  http://localhost:{port}")
        print(f"{'='*50}\n")
        
        # Start server
        uvicorn.run(app, host=host, port=port, reload=reload)
        
    except Exception as e:
        logger.error(f"Failed to start visualization server: {str(e)}")
        raise
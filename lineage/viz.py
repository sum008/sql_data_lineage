"""
Web visualization server for lineage graphs.

This module provides a FastAPI web server with REST API endpoints
for exploring lineage data through an interactive web interface.
"""

from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from lineage.column_builder import ColumnLineageBuilder
from lineage.graph_builder import GraphBuilder
from lineage.search import GraphSearcher
from lineage.config import LoggerSetup, Config, FileProcessError, GraphBuildError


logger = LoggerSetup.get_logger(__name__)


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
            
            self.logger.info("Lineage data loaded successfully")
            
        except (FileProcessError, GraphBuildError) as e:
            self.logger.error(f"Failed to load lineage data: {str(e)}")
            raise
    
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
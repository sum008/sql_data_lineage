from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from lineage.column_builder import build_column_lineage
from lineage.graph_builder import build_graph
from lineage.search import get_upstream_lineage


def run_viz(lineage_json):

    graph = build_graph(lineage_json)

    column_lineage = build_column_lineage(lineage_json)

    app = FastAPI()

    # serve frontend files
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/")
    def index():
        return FileResponse("frontend/index.html")

    @app.get("/graph")
    def get_graph():
        return graph

    @app.get("/lineage/{table}")
    def lineage(table: str):
        return get_upstream_lineage(graph, table)
    
    @app.get("/column-lineage/{table}")
    def renderColumnLineage(table: str):
        return column_lineage.get(table, {})

    print("\nLineage UI running at: http://localhost:8001\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
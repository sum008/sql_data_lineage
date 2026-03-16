from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from .graph_builder import build_graph


def run_viz(lineage_json):

    graph = build_graph(lineage_json)

    app = FastAPI()

    @app.get("/graph")
    def get_graph():
        return graph

    @app.get("/", response_class=HTMLResponse)
    def index():

        return """
            <!DOCTYPE html>
            <html>

            <head>

            <title>SQL Lineage Viewer</title>

            <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
            <script src="https://unpkg.com/dagre/dist/dagre.min.js"></script>
            <script src="https://unpkg.com/cytoscape-dagre/cytoscape-dagre.js"></script>

            <style>

            body{
            font-family: Arial;
            margin:20px;
            }

            #cy{
            width:100%;
            height:85vh;
            border:1px solid #ccc;
            }

            #search{
            padding:8px;
            width:300px;
            margin-bottom:10px;
            }

            </style>

            </head>

            <body>

            <h2>SQL Lineage Graph</h2>

            <input id="search" placeholder="Search table"/>

            <div id="cy"></div>

            <script>

            fetch('/graph')
            .then(r => r.json())
            .then(data => {

                const elements = []

                data.nodes.forEach(n => {
                    elements.push({
                        data:{
                            id:n.id,
                            type:n.type
                        }
                    })
                })

                data.edges.forEach(e => {
                    elements.push({
                        data:{
                            source:e.source,
                            target:e.target
                        }
                    })
                })

                const cy = cytoscape({

                    container: document.getElementById('cy'),

                    elements: elements,

                    style: [

                    {
                    selector: 'node',
                    style:{                    # Byte-compiled / optimized / DLL files
                    __pycache__/
                    *.py[cod]
                    *$py.class
                    
                    # pytest
                    .pytest_cache/
                    
                    # Virtual environments
                    venv/
                    env/
                    ENV/
                    
                    # IDE
                    .vscode/
                    .idea/
                    *.swp
                    *.swo
                    
                    # OS
                    .DS_Store
                    Thumbs.db
                    
                    # Dependencies
                    *.egg-info/
                    dist/
                    build/
                    'label':'data(id)',
                    'text-wrap':'wrap',
                    'text-max-width':'120px',
                    'shape':'round-rectangle',
                    'padding':'10px',
                    'background-color':'#1f77b4',
                    'color':'white',
                    'text-valign':'center',
                    'text-halign':'center',
                    'font-size':12,
                    'width':'label',
                    'height':'label'
                    }
                    },

                    {
                    selector:'node[type="source"]',
                    style:{
                    'background-color':'#2ecc71'
                    }
                    },

                    {
                    selector:'edge',
                    style:{
                    'curve-style':'bezier',
                    'width':2,
                    'line-color':'#888',
                    'target-arrow-shape':'triangle',
                    'target-arrow-color':'#888'
                    }
                    }

                    ],

                    layout:{
                        name:'dagre',
                        rankDir:'LR',
                        nodeSep:80,
                        rankSep:150
                    }

                })


                cy.on('tap','node', function(evt){

                    const node = evt.target

                    cy.elements().removeClass('highlighted')

                    node.addClass('highlighted')
                    node.incomers().addClass('highlighted')
                    node.outgoers().addClass('highlighted')

                })


               document.getElementById("search").addEventListener("input", function(e){

                const val = e.target.value.toLowerCase()

                if(val === ""){
                    cy.elements().style('display','element')
                    return
                }

                cy.elements().style('display','none')

                const matched = cy.nodes().filter(n =>
                    n.id().toLowerCase().includes(val)
                )

                matched.forEach(node => {

                    const upstream = node.predecessors()
                    const downstream = node.successors()

                    node.style('display','element')

                    upstream.style('display','element')
                    downstream.style('display','element')

                    upstream.connectedEdges().style('display','element')
                    downstream.connectedEdges().style('display','element')

                })

            })

            })

            </script>

            </body>
            </html>
            """
    uvicorn.run(app, host="0.0.0.0", port=8001)
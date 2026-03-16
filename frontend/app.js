let cy

function renderGraph(data){

    const elements = []

    data.nodes.forEach(n => {
        elements.push({ data:{ id:n.id } })
    })

    data.edges.forEach(e => {
        elements.push({
            data:{
                source:e.source,
                target:e.target
            }
        })
    })

    if(cy){
        cy.destroy()
    }

    cy = cytoscape({

        container: document.getElementById('cy'),

        elements: elements,

        style: [

        {
            selector:'node',
            style:{
            'label':'data(id)',

            'color':'white',
            'font-size':14,
            'font-weight':'bold',

            'text-wrap':'wrap',
            'text-max-width':'120px',

            'text-valign':'center',
            'text-halign':'center',

            'background-color':'#1f77b4',

            'shape':'round-rectangle',

            'padding':'20px',

            'width':'label',
            'height':'label',

            'min-width':80,
            'min-height':40
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
        rankSep:220,
        nodeSep:150,
        edgeSep:80
        }

    })
    cy.layout({
    name:'dagre',
    rankDir:'LR',
    rankSep:200,
    nodeSep:120
}).run()
}

fetch("/graph")
.then(r => r.json())
.then(data => renderGraph(data))


document.getElementById("search").addEventListener("keydown", function(e){

    if(e.key === "Enter"){

        const table = e.target.value.trim()

        if(!table){
            return
        }

        fetch(`/lineage/${table}`)
        .then(r => r.json())
        .then(data => {
            renderGraph(data)
        })
    }

})

document.getElementById("search").addEventListener("input", function(e){

    if(e.target.value === ""){
        fetch("/graph")
        .then(r => r.json())
        .then(data => renderGraph(data))
    }

})
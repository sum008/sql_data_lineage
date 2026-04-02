let cy
let allTables = []

function renderColumnLineage(data){

    const container = document.getElementById("column-lineage")

    let html = "<h3>Column Lineage</h3>"

    html += "<table>"
    html += "<tr><th>Target Column</th><th>Source Columns</th></tr>"

    Object.entries(data).forEach(([target, sources]) => {

        html += `
        <tr>
            <td><b>${target}</b></td>
            <td>${sources.join("<br>")}</td>
        </tr>`

    })

    html += "</table>"

    container.innerHTML = html
}

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

        'background-color':'#4f46e5',
        'color':'white',

        'font-size':13,
        'font-weight':'bold',

        'shape':'round-rectangle',
        'padding':'16px',

        'text-valign':'center',
        'text-halign':'center',

        'width':'label',
        'height':'label',

        'text-wrap':'wrap',
        'text-max-width':'120px',

        'border-width':2,
        'border-color':'#312e81'
        }
        },
        
        {
        selector:'node.selected',
        style:{
        'background-color':'#ef4444'
        }
        },

        {
        selector:'edge',
        style:{
        'curve-style':'bezier',
        'width':2,
        'line-color':'#94a3b8',
        'target-arrow-shape':'triangle',
        'target-arrow-color':'#94a3b8'
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

    const tooltip = document.getElementById("tooltip")

    cy.on('mouseover', 'node', function(evt){

        const node = evt.target
        tooltip.style.display = "block"
        tooltip.innerHTML = node.id()

    })

    cy.on('mousemove', 'node', function(evt){

        tooltip.style.left = evt.renderedPosition.x + 20 + "px"
        tooltip.style.top = evt.renderedPosition.y + 20 + "px"

    })

    cy.on('mouseout', 'node', function(){

        tooltip.style.display = "none"

    })

    cy.on('tap','node', function(evt){

    cy.nodes().removeClass('selected')

    const node = evt.target
    node.addClass('selected')

    const table = node.id()

    fetch(`/column-lineage/${table}`)
    .then(r => r.json())
    .then(data => renderColumnLineage(data))

})

}

// Tab switching functionality
function setupTabSwitching(){
    const tabButtons = document.querySelectorAll('.tab-button')
    const tabContents = document.querySelectorAll('.tab-content')

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab')
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'))
            tabContents.forEach(content => content.classList.remove('active'))
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active')
            document.getElementById(tabId).classList.add('active')
        })
    })
}

// Render tables list
function renderTablesList(tables){
    const container = document.getElementById('tables-list')
    
    if(tables.length === 0){
        container.innerHTML = '<p>No tables found</p>'
        return
    }
    
    let html = ''
    tables.forEach(table => {
        html += `<div class="table-item" data-table="${table}">${table}</div>`
    })
    
    container.innerHTML = html
    
    // Add click handlers to table items
    document.querySelectorAll('.table-item').forEach(item => {
        item.addEventListener('click', () => {
            selectTable(item.getAttribute('data-table'))
        })
    })
}

// Display table columns
function selectTable(tableName){
    // Update selection styling
    document.querySelectorAll('.table-item').forEach(item => {
        item.classList.remove('selected')
        if(item.getAttribute('data-table') === tableName){
            item.classList.add('selected')
        }
    })
    
    // Fetch and display columns
    fetch(`/tables/${tableName}/columns`)
    .then(r => r.json())
    .then(data => {
        const container = document.getElementById('table-details')
        
        let html = `<h3>${tableName}</h3>`
        
        if(data.columns.length === 0){
            html += '<p>No columns found</p>'
        } else {
            html += '<table class="columns-table">'
            html += '<tr><th>Column Name</th></tr>'
            
            data.columns.forEach(col => {
                html += `<tr><td>${col}</td></tr>`
            })
            
            html += '</table>'
        }
        
        container.innerHTML = html
    })
    .catch(err => {
        const container = document.getElementById('table-details')
        container.innerHTML = `<p>Error loading columns: ${err.message}</p>`
    })
}

// Load all tables on Tables tab initialization
function loadTablesList(){
    fetch('/tables')
    .then(r => r.json())
    .then(data => {
        allTables = data.tables.sort()
        renderTablesList(allTables)
    })
    .catch(err => {
        const container = document.getElementById('tables-list')
        container.innerHTML = `<p>Error loading tables: ${err.message}</p>`
    })
}

// Search functionality in tables tab
function setupTableSearch(){
    const search = document.getElementById('table-search')
    
    search.addEventListener('input', () => {
        const query = search.value.toLowerCase()
        
        if(query === ''){
            renderTablesList(allTables)
        } else {
            const filtered = allTables.filter(table => 
                table.toLowerCase().includes(query)
            )
            renderTablesList(filtered)
        }
    })
}

document.addEventListener("DOMContentLoaded", function(){

    // Initialize tabs
    setupTabSwitching()
    
    // Load tables list for Tables tab
    loadTablesList()
    setupTableSearch()

    // Initialize Lineage tab
    fetch("/graph")
    .then(r => r.json())
    .then(data => renderGraph(data))

    const search = document.getElementById("search")

    search.addEventListener("keydown", function(e){

        if(e.key === "Enter"){

            const table = e.target.value.trim()

            if(!table) return

            fetch(`/lineage/${table}`)
            .then(r => r.json())
            .then(data => renderGraph(data))
        }

    })

    search.addEventListener("input", function(e){

        if(e.target.value === ""){
            fetch("/graph")
            .then(r => r.json())
            .then(data => renderGraph(data))
        }

    })

})
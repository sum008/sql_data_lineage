import json

from lineage.graph_builder import build_graph

def build_graph_indexes(graph):

    target_to_sources = {}
    source_to_targets = {}

    for edge in graph["edges"]:

        src = edge["source"]
        tgt = edge["target"]

        target_to_sources.setdefault(tgt, set()).add(src)
        source_to_targets.setdefault(src, set()).add(tgt)

    return target_to_sources, source_to_targets


def get_upstream_lineage(graph, search_table):
    # Build indexes for quick lookup - narrow down to relevant subgraph
    target_to_sources, _ = build_graph_indexes(graph)
    visited = set()

    def dfs(table):
        if table in visited:
            return
        visited.add(table)
        for source in target_to_sources.get(table, []):
            dfs(source)

    dfs(search_table)
    nodes = [{"id": n} for n in visited]
    edges = [
        edge
        for edge in graph["edges"]
        if edge["source"] in visited and edge["target"] in visited
    ]
    return {
        "nodes": nodes,
        "edges": edges
    }

# if __name__ == "__main__":
#     graph = build_graph("/Users/sumit/Documents/lineage.json")
#     lineage = get_upstream_lineage(graph, "sales_report")
#     json_lineage = json.dumps(lineage, indent=2)
    # print(json_lineage)
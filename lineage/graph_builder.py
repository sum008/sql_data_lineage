import json


def build_graph(lineage_json_path):

    with open(lineage_json_path) as f:
        data = json.load(f)

    nodes = set()
    edges = []

    for entry in data:

        lineage_records = entry["lineage"]

        if isinstance(lineage_records, dict):
            lineage_records = [lineage_records]

        for record in lineage_records:

            target = record["target_table"]
            sources = record["source_tables"]

            nodes.add(target)

            for src in sources:

                nodes.add(src)

                edges.append({
                    "source": src,
                    "target": target
                })

    node_list = [{"id": n} for n in nodes]

    return {
        "nodes": node_list,
        "edges": edges
    }

if __name__ == "__main__":
    graph = build_graph("/Users/sumit/Documents/lineage.json")
    op = json.dumps(graph, indent=2)
    print(op)
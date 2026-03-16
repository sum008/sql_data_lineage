import json

def build_column_lineage(lineage_json_path):

    with open(lineage_json_path) as f:
        data = json.load(f)

    column_lineage = {}

    for entry in data:
        lineage_records = entry["lineage"]
        if isinstance(lineage_records, dict):
            lineage_records = [lineage_records]

        for record in lineage_records:
            target_table = record["target_table"]
            column_lineage.setdefault(target_table, {})
            for column_info in record.get("column_lineage", []):
                column_lineage[target_table][column_info["target_column"]] = column_info["source_columns"]

    return column_lineage

# if __name__ == "__main__":
#     column_lineage = build_column_lineage("/Users/sumit/Documents/lineage.json")
#     op = json.dumps(column_lineage, indent=2)
#     print(op)
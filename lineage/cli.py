import json
from pathlib import Path

from .scanner import find_sql_files, read_sql_file
from .extractor import extract_lineage


def run_scan(input_folder, output_file, target_table=None):

    sql_files = find_sql_files(input_folder)

    results = []

    for file in sql_files:

        sql_text = read_sql_file(file)

        try:
            lineage = extract_lineage(sql_text, target_table)
            if lineage:
                results.append({
                    "file": str(file),
                    "lineage": lineage
                })

        except Exception as e:

            results.append({
                "file": str(file),
                "error": str(e)
            })

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Processed {len(sql_files)} SQL files")
    print(f"Output written to {output_file}")
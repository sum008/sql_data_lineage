import os
from pathlib import Path


def find_sql_files(folder):

    sql_files = []

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".sql"):
                sql_files.append(Path(root) / file)

    return sql_files


def read_sql_file(path):
    with open(path, "r") as f:
        return f.read()
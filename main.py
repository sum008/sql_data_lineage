import argparse
from lineage.cli import run_scan


def main():

    parser = argparse.ArgumentParser(
        description="SQL Lineage Extractor"
    )

    subparsers = parser.add_subparsers(dest="command")

    viz_parser = subparsers.add_parser(
        "viz",
        help="visualize lineage graph"
    )

    viz_parser.add_argument(
        "lineage_json",
        help="path to lineage json"
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="scan folder for SQL lineage"
    )

    scan_parser.add_argument(
        "input_folder",
        help="folder containing SQL scripts"
    )

    scan_parser.add_argument(
        "--output",
        required=True,
        help="output JSON file"
    )

    scan_parser.add_argument(
        "--target",
        help="extract lineage only for this target table"
    )

    args = parser.parse_args()

    if args.command == "scan":
        run_scan(args.input_folder, args.output, args.target)
    elif args.command == "viz":
        from lineage.viz import run_viz
        run_viz(args.lineage_json)


if __name__ == "__main__":
    main()
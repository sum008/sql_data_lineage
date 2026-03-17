"""
SQL Data Lineage - Main entry point.

A comprehensive tool for extracting, analyzing, and visualizing SQL data lineage.
"""

import argparse
import sys
from typing import Optional

from lineage.cli import LineageScanProcessor
from lineage.viz import run_viz
from lineage.config import LoggerSetup, Config, LineageException


logger = LoggerSetup.get_logger(__name__)


class LineageApp:
    """Main application class for command-line interface."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = LoggerSetup.get_logger(__name__)
    
    def run(self, args: Optional[list] = None) -> int:
        """
        Run the application based on command-line arguments.
        
        Args:
            args: Command-line arguments (uses sys.argv if None)
            
        Returns:
            Exit code (0 for success, 1 for error)
        """
        parser = self._build_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            if parsed_args.command == "scan":
                return self._handle_scan_command(parsed_args)
            elif parsed_args.command == "viz":
                return self._handle_viz_command(parsed_args)
            else:
                parser.print_help()
                return 0
        
        except LineageException as e:
            self.logger.error(f"Lineage error: {str(e)}")
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
            return 1
    
    def _handle_scan_command(self, args) -> int:
        """
        Handle the 'scan' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code
        """
        self.logger.info(
            f"Starting lineage scan: {args.input_folder} -> {args.output}"
        )
        
        processor = LineageScanProcessor()
        processor.process_folder(
            args.input_folder,
            args.output,
            args.target
        )
        
        self.logger.info("Scan completed successfully")
        return 0
    
    def _handle_viz_command(self, args) -> int:
        """
        Handle the 'viz' command.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Exit code (never returns on success, server runs indefinitely)
        """
        self.logger.info(f"Starting visualization server: {args.lineage_json}")
        
        run_viz(args.lineage_json)
        
        return 0
    
    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """
        Build the argument parser.
        
        Returns:
            ArgumentParser with all commands and options configured
        """
        parser = argparse.ArgumentParser(
            prog="SQL Data Lineage",
            description="Extract and visualize SQL data lineage from SQL scripts",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Scan folder for SQL files and extract lineage
  python main.py scan ./sql_scripts --output lineage.json
  
  # Scan and filter for specific table
  python main.py scan ./sql_scripts --output lineage.json --target sales_summary
  
  # Visualize lineage in interactive web interface
  python main.py viz lineage.json
            """
        )
        
        subparsers = parser.add_subparsers(
            dest="command",
            help="Command to run",
            required=False
        )
        
        # ======================== SCAN COMMAND ========================
        scan_parser = subparsers.add_parser(
            "scan",
            help="Scan folder for SQL files and extract lineage",
            description="Recursively scan a folder for SQL files and extract lineage "
                       "information from each file"
        )
        
        scan_parser.add_argument(
            "input_folder",
            metavar="INPUT_FOLDER",
            help="Path to folder containing SQL scripts"
        )
        
        scan_parser.add_argument(
            "--output",
            "-o",
            required=True,
            metavar="OUTPUT_FILE",
            help="Path to output JSON file for lineage results"
        )
        
        scan_parser.add_argument(
            "--target",
            "-t",
            metavar="TABLE_NAME",
            help="Extract lineage only for this target table (optional)"
        )
        
        # ======================== VIZ COMMAND ========================
        viz_parser = subparsers.add_parser(
            "viz",
            help="Visualize lineage graph in web interface",
            description="Start a web server to interactively explore the lineage graph"
        )
        
        viz_parser.add_argument(
            "lineage_json",
            metavar="LINEAGE_JSON",
            help="Path to lineage JSON file (created by 'scan' command)"
        )
        
        return parser


def main():
    """Main entry point."""
    app = LineageApp()
    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
import argparse
import sys
from pathlib import Path
import logging

from .extractor import extract_from_pbix
from .generator import generate_queries_md, generate_dependency_graph_json
from .dependency import detect_dependencies_regex


def setup_logging(log_level: str):
    level = logging.INFO if log_level == "INFO" else logging.DEBUG
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_pbix(pbix_path: Path, output_dir: Path, overwrite: bool, parser_mode: str):
    logging.info(f"Processing PBIX: {pbix_path}")
    try:
        nodes = extract_from_pbix(pbix_path)
        logging.info(f"Extracted {len(nodes)} nodes")

        # Create output directory
        pbix_name = pbix_path.stem
        out_dir = output_dir / pbix_name
        if out_dir.exists() and not overwrite:
            logging.error(f"Output directory {out_dir} exists and --overwrite not set")
            return False
        out_dir.mkdir(parents=True, exist_ok=True)

        # Generate outputs
        queries_md_path = out_dir / "queries.md"
        dependency_json_path = out_dir / "dependency_graph.json"

        # Detect dependencies
        edges = detect_dependencies_regex(nodes)

        generate_queries_md(nodes, edges, queries_md_path, pbix_name)
        generate_dependency_graph_json(nodes, dependency_json_path, pbix_name, parser_mode)

        logging.info(f"Output saved to %s", out_dir)
        return True
    except Exception:
        logging.exception("Failed to process %s", pbix_path)
        return False

def main():
    parser = argparse.ArgumentParser(description="PBIX Model Extractor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract Power Query from PBIX files")
    extract_parser.add_argument("path", help="Path to PBIX file or directory containing PBIX files")
    extract_parser.add_argument("--out", default="1_OUTPUT", help="Output directory (default: 1_OUTPUT)")
    extract_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output directories")
    extract_parser.add_argument("--parser", choices=["regex", "ast"], default="regex", help="Parser mode (default: regex)")
    extract_parser.add_argument("--log-level", choices=["INFO", "DEBUG"], default="INFO", help="Log level (default: INFO)")

    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.command == "extract":
        path = Path(args.path)
        output_dir = Path(args.out)

        if path.is_file():
            if path.suffix.lower() == '.pbix':
                success = extract_pbix(path, output_dir, args.overwrite, args.parser)
                sys.exit(0 if success else 1)
            else:
                logging.error("File must have .pbix extension")
                sys.exit(1)
        elif path.is_dir():
            pbix_files = list(path.glob('*.pbix'))
            if not pbix_files:
                logging.error("No .pbix files found in directory")
                sys.exit(1)
            success_count = 0
            for pbix_file in pbix_files:
                if extract_pbix(pbix_file, output_dir, args.overwrite, args.parser):
                    success_count += 1
            logging.info(f"Processed {success_count}/{len(pbix_files)} files successfully")
            sys.exit(0 if success_count == len(pbix_files) else 1)
        else:
            logging.error("Path does not exist")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Requirements Tracer - Unified CLI Tool
=======================================

Traces parent-child relationships across requirement files (DOORS 18-column schema).

Usage:
    python requirements_tracer.py -c example.cfg
    python requirements_tracer.py -c example.cfg -o output/custom/
    python requirements_tracer.py -c example.cfg --debug
    python requirements_tracer.py -c example.cfg --no-filter -v

Author: Christopher Granabetter Ifa - UVIE
Date: April 2026
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from utils.tracer.config import load_config, TracerConfig
from utils.tracer.loader import load_requirements
from utils.tracer.tracer import RequirementsTracer
from utils.tracer.exporter import export_ancestry_xlsx, write_debug_files


def run_trace(
    config: TracerConfig,
    output_dir: Optional[str] = None,
    debug: Optional[bool] = None,
    no_filter: bool = False,
) -> int:
    """
    Run the tracer from an already loaded config object.

    Args:
        config: Parsed TracerConfig instance.
        output_dir: Override output directory (uses config value if None).
        debug: Write debug JSON files; overrides config flag when set.
        no_filter: Skip redundant-ancestry filtering when True.

    Returns:
        0 on success, 1 on error.
    """
    log = logging.getLogger(__name__)

    resolved_output_dir = output_dir or config.output_dir
    resolved_debug = config.debug if debug is None else debug
    Path(resolved_output_dir).mkdir(parents=True, exist_ok=True)

    tracer = RequirementsTracer()

    for src in config.sources:
        try:
            entries = load_requirements(src.filepath, src.sheet, src.label)
        except (FileNotFoundError, ValueError) as exc:
            log.error("Failed to load source '%s': %s", src.label, exc)
            return 1
        tracer.add_source(entries)

    tracer.set_hierarchy(config.hierarchy)

    for src in config.extra_links:
        try:
            entries = load_requirements(src.filepath, src.sheet, src.label)
        except (FileNotFoundError, ValueError) as exc:
            log.error("Failed to load extra source '%s': %s", src.label, exc)
            return 1
        tracer.link_extra(entries)

    log.info("Building trace...")
    ancestry = tracer.trace()

    if resolved_debug:
        write_debug_files(tracer, ancestry, resolved_output_dir, "after_scrape")
    tracer.verify_coverage(ancestry, "after_scrape")

    if not no_filter:
        ancestry = tracer.filter_redundant(ancestry)
        tracer.verify_coverage(ancestry, "after_filter")
        if resolved_debug:
            write_debug_files(tracer, ancestry, resolved_output_dir, "after_filter")

    xlsx_path = str(Path(resolved_output_dir) / config.export_xlsx)
    export_ancestry_xlsx(tracer, ancestry, xlsx_path)

    log.info("Done.")
    return 0


def main(argv=None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="reqtracer",
        description=(
            "Trace parent-child relationships across requirement files "
            "(DOORS 18-column schema)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a config file
  %(prog)s -c example.cfg

  # Override output directory
  %(prog)s -c example.cfg -o output/custom/

  # Enable debug file output
  %(prog)s -c example.cfg --debug

  # Skip redundant-ancestry filtering
  %(prog)s -c example.cfg --no-filter

  # Verbose logging
  %(prog)s -c example.cfg -v
        """,
    )

    parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to the .cfg configuration file.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Override the output directory from config.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Write debug JSON files (overrides config setting).",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip redundant-ancestry filtering (export all rows).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG-level) logging.",
    )

    args = parser.parse_args(argv)

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)-8s %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger(__name__)

    # Load and validate config
    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        log.error("Configuration error: %s", exc)
        return 1

    return run_trace(
        config,
        output_dir=args.output_dir,
        debug=args.debug,
        no_filter=args.no_filter,
    )


if __name__ == "__main__":
    sys.exit(main())

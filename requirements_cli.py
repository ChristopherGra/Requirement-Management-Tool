#!/usr/bin/env python3
"""Unified CLI for normalization, tracing, and the end-to-end pipeline."""

import argparse
import logging
import sys

import requirements_processor
import requirements_tracer
from utils.tracer.pipeline import run_normalize_and_trace


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="requirements-cli",
        description=(
            "Unified entry point for requirements normalization, tracing, "
            "and normalize-then-trace workflows."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    manage_parser = subparsers.add_parser(
        "manage",
        help="Run the requirements normalization tool.",
    )
    manage_parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to requirements_processor.py",
    )

    trace_parser = subparsers.add_parser(
        "trace",
        help="Run the requirements tracer.",
    )
    trace_parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to requirements_tracer.py",
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Normalize configured sources, then run the tracer on them.",
    )
    pipeline_parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to the tracer configuration file describing the source hierarchy.",
    )
    pipeline_parser.add_argument(
        "-o",
        "--output-dir",
        help="Override the trace output directory from the config.",
    )
    pipeline_parser.add_argument(
        "--normalized-dir",
        help="Directory for the intermediate normalized files.",
    )
    pipeline_parser.add_argument(
        "--debug",
        action="store_true",
        default=None,
        help="Force tracer debug file output.",
    )
    pipeline_parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Skip redundant-ancestry filtering during trace export.",
    )
    pipeline_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable INFO/DEBUG logging for the pipeline.",
    )

    args = parser.parse_args(argv)

    if args.command == "manage":
        return requirements_processor.main(args.args)

    if args.command == "trace":
        return requirements_tracer.main(args.args)

    if args.command == "pipeline":
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format="%(levelname)-8s %(message)s",
            stream=sys.stdout,
        )
        _, generated_config_path = run_normalize_and_trace(
            cfg_path=args.config,
            normalized_dir=args.normalized_dir,
            output_dir=args.output_dir,
            debug=args.debug,
            no_filter=args.no_filter,
        )
        print(f"Generated pipeline config: {generated_config_path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
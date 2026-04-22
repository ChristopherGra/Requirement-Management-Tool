"""Normalize configured sources, then run the tracer on the normalized outputs."""

from __future__ import annotations

import configparser
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from requirements_processor import process_single_file
from utils.tracer.config import SourceEntry, TracerConfig, load_config
from requirements_tracer import run_trace
from utils import FileCache

log = logging.getLogger(__name__)


def run_normalize_and_trace(
    cfg_path: str | Path,
    normalized_dir: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    debug: Optional[bool] = None,
    no_filter: bool = False,
) -> Tuple[TracerConfig, Path]:
    """Run the management pipeline first, then trace the normalized outputs."""
    cfg_path = Path(cfg_path).resolve()
    config = load_config(str(cfg_path))

    trace_output_dir = Path(output_dir or config.output_dir).resolve()
    normalized_output_dir = Path(
        normalized_dir or trace_output_dir / "normalized_for_trace"
    ).resolve()
    normalized_output_dir.mkdir(parents=True, exist_ok=True)

    cache = FileCache()
    generated_config = _build_generated_config(
        config=config,
        normalized_dir=normalized_output_dir,
        trace_output_dir=trace_output_dir,
        cache=cache,
        debug=debug,
    )

    generated_config_path = normalized_output_dir / "trace_pipeline.generated.cfg"
    write_generated_trace_config(generated_config_path, generated_config)

    log.info("Running tracer against normalized sources...")
    run_trace(
        generated_config,
        output_dir=str(trace_output_dir),
        debug=generated_config.debug,
        no_filter=no_filter,
    )
    return generated_config, generated_config_path


def _build_generated_config(
    config: TracerConfig,
    normalized_dir: Path,
    trace_output_dir: Path,
    cache: FileCache,
    debug: Optional[bool] = None,
) -> TracerConfig:
    """Normalize all configured inputs and build a trace config for the outputs."""
    normalized_sources: Dict[Tuple[str, Optional[str]], Path] = {}

    def normalize_entry(entry: SourceEntry) -> SourceEntry:
        key = (entry.filepath, entry.sheet)
        if key not in normalized_sources:
            output_path = normalized_dir / f"{_slugify_label(entry.label)}_normalized.xlsx"
            log.info(
                "Normalizing source '%s' from %s%s",
                entry.label,
                entry.filepath,
                f" [sheet: {entry.sheet}]" if entry.sheet else "",
            )
            success = process_single_file(
                Path(entry.filepath),
                output_path=output_path,
                cache=cache,
                sheet_name=entry.sheet,
            )
            if not success:
                raise ValueError(f"Failed to normalize source '{entry.label}'")
            normalized_sources[key] = output_path.resolve()

        return SourceEntry(
            label=entry.label,
            filepath=str(normalized_sources[key]),
            sheet=None,
        )

    generated_sources = [normalize_entry(source) for source in config.sources]
    generated_extra_links = [normalize_entry(source) for source in config.extra_links]

    return TracerConfig(
        output_dir=str(trace_output_dir),
        sources=generated_sources,
        hierarchy=list(config.hierarchy),
        extra_links=generated_extra_links,
        export_xlsx=config.export_xlsx,
        debug=config.debug if debug is None else debug,
    )


def write_generated_trace_config(output_path: Path, config: TracerConfig) -> None:
    """Persist the generated config so the pipeline remains reproducible."""
    parser = configparser.ConfigParser()
    parser.optionxform = str

    parser["general"] = {
        "output_dir": config.output_dir,
        "debug": str(config.debug).lower(),
    }
    parser["sources"] = {
        entry.label: entry.filepath for entry in config.sources
    }
    parser["hierarchy"] = {
        "order": ", ".join(config.hierarchy)
    }
    if config.extra_links:
        parser["extra_links"] = {
            entry.label: entry.filepath for entry in config.extra_links
        }
    parser["export"] = {
        "ancestry_xlsx": config.export_xlsx
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file_handle:
        parser.write(file_handle)


def _slugify_label(label: str) -> str:
    """Convert a trace label into a filesystem-safe stem."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", label.strip()).strip("_")
    return slug.lower() or "source"

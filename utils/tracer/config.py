import configparser
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


@dataclass
class SourceEntry:
    """A single data source: label + xlsx filepath + optional sheet name."""
    label: str
    filepath: str
    sheet: Optional[str] = None


@dataclass
class TracerConfig:
    """All settings parsed from a .cfg file."""
    output_dir: str = "output"
    sources: List[SourceEntry] = field(default_factory=list)
    hierarchy: List[str] = field(default_factory=list)
    extra_links: List[SourceEntry] = field(default_factory=list)
    export_xlsx: str = "ancestry_trace.xlsx"
    debug: bool = False


def load_config(cfg_path: str) -> TracerConfig:
    """Parse a .cfg file and return a TracerConfig."""
    cfg_path = Path(cfg_path).resolve()
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    parser = configparser.ConfigParser()
    parser.optionxform = str  # preserve key case
    parser.read(cfg_path)

    config = TracerConfig()
    base_dir = cfg_path.parent

    # [general]
    if parser.has_section("general"):
        config.output_dir = parser.get("general", "output_dir", fallback="output")
        config.debug = parser.getboolean("general", "debug", fallback=False)

    # [sources]
    if parser.has_section("sources"):
        for label, value in parser.items("sources"):
            se = _parse_source_entry(label, value, base_dir)
            config.sources.append(se)
            log.info("Source: %s -> %s (sheet: %s)", se.label, se.filepath, se.sheet)

    # [hierarchy]
    if parser.has_section("hierarchy"):
        order_str = parser.get("hierarchy", "order", fallback="")
        config.hierarchy = [s.strip() for s in order_str.split(",") if s.strip()]

    # [extra_links]
    if parser.has_section("extra_links"):
        for label, value in parser.items("extra_links"):
            se = _parse_source_entry(label, value, base_dir)
            config.extra_links.append(se)
            log.info("Extra link: %s -> %s (sheet: %s)", se.label, se.filepath, se.sheet)

    # [export]
    if parser.has_section("export"):
        config.export_xlsx = parser.get("export", "ancestry_xlsx", fallback="ancestry_trace.xlsx")

    _validate_config(config)
    return config


def _parse_source_entry(label: str, value: str, base_dir: Path) -> SourceEntry:
    """Parse 'filepath [:: sheet_name]' into a SourceEntry."""
    parts = value.split("::")
    filepath = parts[0].strip()
    sheet = parts[1].strip() if len(parts) > 1 else None
    if not Path(filepath).is_absolute():
        filepath = str((base_dir / filepath).resolve())
    return SourceEntry(label=label, filepath=filepath, sheet=sheet)


def _validate_config(config: TracerConfig) -> None:
    """Check config consistency (does not check file existence)."""
    source_labels = {s.label for s in config.sources}
    for label in config.hierarchy:
        if label not in source_labels:
            raise ValueError(
                f"Hierarchy label '{label}' not found in [sources]. "
                f"Available: {source_labels}"
            )
    if not config.sources:
        raise ValueError("No [sources] defined in config file.")
    if not config.hierarchy:
        raise ValueError("No [hierarchy] order defined in config file.")

"""
compliance_matrix.py — Dissect an annotated ancestry output back into per-source
normalized compliance matrices.

Workflow:
  1. The ancestry xlsx/csv was manually annotated in Excel (Compliance, Applicability, etc.)
  2. This script reads the annotated ancestry file and the original .cfg
  3. For each source in the cfg it extracts the rows that belong to that source
     by matching RequirementIDs against the per-source normalized files produced
     by the pipeline (output/normalized_for_trace/<slug>_normalized.xlsx)
  4. Writes one output file per source named:
       <sheet_or_label>_normalized_compliance_matrix.csv  (or .xlsx)
     placed in <output_dir>/compliance/

Usage:
  python compliance_matrix.py -c example.cfg
  python compliance_matrix.py -c example.cfg --ancestry output/ancestry_trace_new.xlsx
  python compliance_matrix.py -c example.cfg --output-dir output/compliance/
  python compliance_matrix.py -c example.cfg --normalized-dir output/normalized_for_trace/
  python compliance_matrix.py -c example.cfg --fmt xlsx
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from utils.constants import COLUMNS
from utils.tracer.config import load_config, TracerConfig, SourceEntry, slugify_label

log = logging.getLogger(__name__)

# All DOORS columns we want in the output (standard 18-col schema)
OUTPUT_COLS = list(COLUMNS)


def _load_df(path: Path, sheet: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls", ".xlsm"):
        kwargs = {"sheet_name": sheet} if sheet else {}
        df = pd.read_excel(path, dtype=str, **kwargs)
    elif suffix == ".csv":
        df = pd.read_csv(path, dtype=str, sep=";")
        if df.shape[1] == 1:
            df = pd.read_csv(path, dtype=str, sep=",")
    else:
        raise ValueError(f"Unsupported format: {suffix}")
    return df.fillna("")


def _find_normalized_file(label: str, normalized_dir: Path) -> Path | None:
    """Locate the per-source normalized file produced by the pipeline."""
    slug = slugify_label(label)
    for ext in ("xlsx", "csv"):
        candidate = normalized_dir / f"{slug}_normalized.{ext}"
        if candidate.exists():
            return candidate
    return None


def _load_source_df(entry: SourceEntry, normalized_dir: Path) -> pd.DataFrame | None:
    """Load the normalized (or original) source dataframe for this entry."""
    norm_file = _find_normalized_file(entry.label, normalized_dir)
    if norm_file:
        log.debug("Loading source data for %r from %s", entry.label, norm_file)
        df = _load_df(norm_file)
        if "RequirementID" in df.columns:
            return df

    # Fallback: original source file
    src_path = Path(entry.filepath)
    if src_path.exists():
        log.debug("Falling back to source file %s (sheet=%s)", src_path, entry.sheet)
        df = _load_df(src_path, entry.sheet)
        col_map = {c.lower(): c for c in df.columns}
        req_col = col_map.get("requirementid")
        if req_col:
            df = df.rename(columns={req_col: "RequirementID"})
            return df

    log.warning("Could not resolve source data for %r", entry.label)
    return None


def _output_stem(entry: SourceEntry) -> str:
    """Build a unique, readable stem for the output file."""
    if entry.sheet:
        # Use the sheet name (sanitised) since multiple sources share one file
        stem = entry.sheet.strip().replace(" ", "_").replace("/", "_")
    else:
        stem = Path(entry.filepath).stem
        if stem.endswith("_normalized"):
            stem = stem[: -len("_normalized")]
    return stem


def _nearest_ancestor(row: pd.Series, ancestor_cols: list[str]) -> str:
    """Return the first non-empty value from ancestor_cols (nearest first)."""
    for col in ancestor_cols:
        val = str(row.get(col, "")).strip()
        if val:
            return val
    return ""


def _extract_rows(
    ancestry: pd.DataFrame,
    req_ids: set[str],
    source_df: pd.DataFrame | None,
    ancestor_cols: list[str] | None = None,
    level_col: str | None = None,
) -> pd.DataFrame:
    """
    Extract and assemble rows for one source.

    ancestor_cols: if set, overwrite ParentID with the nearest non-empty value
                  from this ordered list of ancestry level columns (closest first).
                  Used for extra_links (e.g. UVIE) to substitute the nearest
                  top-level ancestor instead of the internal UVIE parent.
    level_col: the ancestry column that stores IDs for this source (e.g.
               "Level 3 (ASW Req)").  When a requirement is an ancestor of a
               more-derived leaf it won't appear in RequirementID; this column
               lets us find and include it anyway.
    """
    rows = ancestry[ancestry["RequirementID"].str.strip().isin(req_ids)].copy()
    missing = [c for c in OUTPUT_COLS if c not in ancestry.columns]
    for m in missing:
        rows[m] = ""
        log.warning("Column %r missing from ancestry — blanked in output", m)

    # Restore Definition from the original source document
    if source_df is not None and "Definition" in source_df.columns:
        orig = (
            source_df[["RequirementID", "Definition"]]
            .copy()
            .rename(columns={"Definition": "_orig_def"})
        )
        orig["RequirementID"] = orig["RequirementID"].str.strip()
        rows["RequirementID"] = rows["RequirementID"].str.strip()
        rows = rows.merge(orig, on="RequirementID", how="left")
        rows["Definition"] = rows["_orig_def"].where(
            rows["_orig_def"].notna() & (rows["_orig_def"].str.strip() != ""),
            rows["Definition"],
        )
        rows = rows.drop(columns=["_orig_def"])

    # Drop rows with no RequirementID and no ParentID (blank spacer rows)
    rows = rows[~((rows["RequirementID"].str.strip() == "") & (rows["ParentID"].str.strip() == ""))]

    # For extra_links (e.g. UVIE): substitute ParentID with the nearest ancestor.
    # ancestor_cols is ordered nearest→most-abstract; we pick the first non-empty.
    if ancestor_cols:
        rows["ParentID"] = rows.apply(
            lambda r: _nearest_ancestor(r, ancestor_cols), axis=1
        )

    # Some requirements only appear as ancestors (values inside level_col) rather
    # than as leaf rows.  Find any such IDs and pull them straight from source_df.
    if level_col and level_col in ancestry.columns and source_df is not None:
        already_found = set(rows["RequirementID"].str.strip())
        remaining = req_ids - already_found
        if remaining:
            found_in_level: set[str] = set()
            for cell in ancestry[level_col].fillna(""):
                for rid in str(cell).split("\n"):
                    rid = rid.strip()
                    if rid in remaining:
                        found_in_level.add(rid)
            if found_in_level:
                extra = source_df[
                    source_df["RequirementID"].str.strip().isin(found_in_level)
                ].copy()
                for m in [c for c in OUTPUT_COLS if c not in extra.columns]:
                    extra[m] = ""
                extra = extra[
                    ~(
                        (extra["RequirementID"].str.strip() == "")
                        & (extra["ParentID"].str.strip() == "")
                    )
                ]
                rows = pd.concat([rows, extra[OUTPUT_COLS]], ignore_index=True)
                log.debug(
                    "Added %d ancestor-only rows via %s", len(extra), level_col
                )

    return rows[OUTPUT_COLS].reset_index(drop=True)


def _write(df: pd.DataFrame, path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "xlsx":
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, sep=";", index=False, quotechar='"')
    print(f"  [{len(df):>4} rows] {path}")


def run(
    cfg_path: str,
    ancestry_path: str | None,
    output_dir: str | None,
    normalized_dir: str | None,
    fmt: str,
) -> None:
    config = load_config(cfg_path)
    cfg_dir = Path(cfg_path).resolve().parent

    # Resolve ancestry path: CLI arg > [export] section > default
    if ancestry_path:
        anc_path = Path(ancestry_path)
    else:
        anc_path = cfg_dir / config.output_dir / config.export_xlsx
    if not anc_path.exists():
        sys.exit(f"Ancestry file not found: {anc_path}")

    # Resolve normalized_for_trace dir
    norm_dir = (
        Path(normalized_dir)
        if normalized_dir
        else cfg_dir / config.output_dir / "normalized_for_trace"
    )

    # Resolve output dir
    out_dir = (
        Path(output_dir)
        if output_dir
        else cfg_dir / config.output_dir / "compliance"
    )

    print(f"Ancestry       : {anc_path}")
    print(f"Normalized dir : {norm_dir}")
    print(f"Output         : {out_dir}")
    print()

    ancestry = _load_df(anc_path)

    # All sources: hierarchy + extra_links (deduplicated by label)
    all_sources: dict[str, SourceEntry] = {s.label: s for s in config.sources}
    for s in config.extra_links:
        if s.label not in all_sources:
            all_sources[s.label] = s

    extra_labels = {e.label for e in config.extra_links}
    # Ordered list of level columns nearest→most-abstract, for UVIE parent substitution
    ancestor_cols_for_extra = (
        [f"Level {i} ({label})" for i, label in reversed(list(enumerate(config.hierarchy)))]
        + ["Level -1 (External)"]
    )

    hierarchy_list = list(config.hierarchy)

    for label, entry in all_sources.items():
        source_df = _load_source_df(entry, norm_dir)
        if source_df is None or "RequirementID" not in source_df.columns:
            print(f"  [   0 rows] {label!r} — could not resolve source IDs (check normalized_dir)")
            continue

        # For extra_links (UVIE etc.) replace ParentID with the nearest ancestor
        ancestor_cols = ancestor_cols_for_extra if label in extra_labels else None

        # Determine the level column for this source so we can also pick up
        # requirements that appear only as ancestors (not as leaf RequirementID).
        if label in hierarchy_list:
            lvl_idx = hierarchy_list.index(label)
            level_col: str | None = f"Level {lvl_idx} ({label})"
        else:
            level_col = None

        req_ids = set(source_df["RequirementID"].str.strip().dropna())
        rows = _extract_rows(ancestry, req_ids, source_df, ancestor_cols, level_col)
        stem = _output_stem(entry)
        dest = out_dir / f"{stem}_normalized_compliance_matrix.{fmt}"
        _write(rows, dest, fmt)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dissect annotated ancestry back into per-source compliance matrices."
    )
    parser.add_argument("-c", "--config", required=True, help="Path to .cfg file")
    parser.add_argument(
        "--ancestry",
        default=None,
        help="Path to annotated ancestry file (overrides cfg export path)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for output files (default: <output_dir>/compliance/)",
    )
    parser.add_argument(
        "--normalized-dir",
        default=None,
        help="Directory containing per-source normalized files (default: <output_dir>/normalized_for_trace/)",
    )
    parser.add_argument(
        "--fmt",
        choices=["csv", "xlsx"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )
    run(args.config, args.ancestry, args.output_dir, args.normalized_dir, args.fmt)


if __name__ == "__main__":
    main()


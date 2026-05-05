import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from utils.constants import COLUMNS, COLUMN_MAPPING
from utils.base_processor import Requirement

log = logging.getLogger(__name__)

# Column aliases used when raw CSV columns don't match the DOORS schema names.
_CSV_ALIASES = {k: v for k, v in COLUMN_MAPPING.items()}


def load_requirements(
    filepath: str,
    sheet: Optional[str],
    label: str,
    id_template: Optional[str] = None,
) -> List[Dict]:
    """Load requirements from an xlsx or CSV file.

    Args:
        filepath:    Path to the source file.
        sheet:       Sheet name for xlsx (ignored for CSV).
        label:       Label to tag every loaded requirement with.
        id_template: Optional template to synthesise RequirementID from raw
                     columns, e.g. ``R-{Cat}-{N}/{Type}``.

    Returns:
        List of dicts, each with keys 'requirement', 'deleted', 'label'.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    log.info("Loading '%s' from %s (sheet: %s)", label, filepath, sheet or "all")

    fname = path.name.upper()
    if ".CSV" in fname or ".TSV" in fname:
        delim = ";" if "SEMICOLON" in fname or "SC" in fname else ","
        df = pd.read_csv(filepath, sep=delim, dtype=str, keep_default_na=False)
        # Apply column aliases (case-insensitive) so DOORS names are used downstream
        df = df.rename(columns={c: _CSV_ALIASES[c.lower()] for c in df.columns if c.lower() in _CSV_ALIASES})
        if id_template:
            col_lk = {c.lower(): c for c in df.columns}
            parts = re.split(r"\{[^}]+\}", id_template)
            phs = re.findall(r"\{([^}]+)\}", id_template)
            ids = pd.Series([parts[0]] * len(df), index=df.index)
            for i, ph in enumerate(phs):
                col = col_lk.get(ph.lower())
                ids = ids + (df[col].astype(str).str.strip() if col else "") + parts[i + 1]
            df["RequirementID"] = ids
            log.info("  Synthesised RequirementID using template: %s", id_template)
        entries = _entries_from_df(df, label, source_name=path.name)
        log.info("  Loaded %d requirements as '%s'", len(entries), label)
        return entries

    excel_file = pd.ExcelFile(filepath)

    if sheet:
        if sheet not in excel_file.sheet_names:
            raise ValueError(
                f"Sheet '{sheet}' not found in {filepath}. "
                f"Available sheets: {excel_file.sheet_names}"
            )
        sheets = [sheet]
    else:
        sheets = excel_file.sheet_names

    entries: List[Dict] = []
    for sheet_name in sheets:
        df = excel_file.parse(sheet_name)
        df.columns = df.columns.str.replace(" ", "")
        entries.extend(_entries_from_df(df, label, source_name=sheet_name))

    log.info("  Loaded %d requirements as '%s'", len(entries), label)
    return entries


def _entries_from_df(df: pd.DataFrame, label: str, source_name: str) -> List[Dict]:
    """Shared: validate, normalise and convert a DataFrame to requirement dicts."""
    missing = [col for col in ("RequirementID", "ParentID") if col not in df.columns]
    if missing:
        log.warning("'%s' missing critical columns: %s — skipping", source_name, missing)
        return []

    # Ensure all 18 schema columns exist
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Normalize values
    df[COLUMNS] = df[COLUMNS].fillna("").astype(str)
    df["RequirementID"] = (
        df["RequirementID"].str.replace(r"[\n\r]+", " ", regex=True).str.strip()
    )
    df["ParentID"] = (
        df["ParentID"]
        .str.replace(r"[\n\r,]+", " ", regex=True)
        .str.replace(r"\b(and|or|the|an?)\b", "", regex=True)
        .str.replace("(PRD TBD)", "", regex=False)
        .str.strip()
        .str.replace(r" +", "\n", regex=True)
    )

    # Detect rows containing "deleted" in any column (except UpdatesMade, Definition)
    df["_deleted"] = df[COLUMNS].apply(
        lambda row: next(
            (
                col
                for col in COLUMNS
                if "deleted" in str(row[col]).lower()
                and col not in ("UpdatesMade", "Definition")
            ),
            "",
        ),
        axis=1,
    )

    # Drop empty IDs, explode multi-value RequirementID
    df = df[df["RequirementID"] != ""].copy()
    df["_req_ids"] = df["RequirementID"].str.split()

    req_df = df.explode("_req_ids")
    req_df = req_df[req_df["_req_ids"].str.strip() != ""].copy()
    req_df["_req_ids"] = req_df["_req_ids"].str.strip()
    req_df = req_df.set_index("_req_ids")

    entries: List[Dict] = []
    for req_id, row in req_df.iterrows():
        req = Requirement(
            requirement_id=req_id,
            parent_id=row["ParentID"],
            type=row["Type"],
            sub_type=row["SubType"],
            title=row["Title"],
            definition=row["Definition"],
            notes=row["Notes"],
            remarks=row["Remarks"],
            responsibility=row["Responsibility"],
            subsystem_applicability=row["SubSysApplicability"],
            applicability=row["Applicability"],
            compliance=row["Compliance"],
            compliance_notes=row["ComplianceNotes"],
            verification=row["Verification"],
            verification_notes=row["VerificationNotes"],
            reference_document=row["ReferenceDocument"],
            original_esa_identifier=row["OriginalESAIdentifier"],
            updates_made=row["UpdatesMade"],
        )
        entries.append({
            "requirement": req,
            "deleted": row["_deleted"],
            "label": label,
        })

    return entries

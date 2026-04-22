import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from utils.constants import COLUMNS
from utils.base_processor import Requirement

log = logging.getLogger(__name__)


def load_requirements(filepath: str, sheet: Optional[str], label: str) -> List[Dict]:
    """Load requirements from an xlsx file / sheet.

    Args:
        filepath: Path to the xlsx file.
        sheet:    Sheet name to load, or None to load all sheets.
        label:    Label to tag every loaded requirement with.

    Returns:
        List of dicts, each with keys 'requirement', 'deleted', 'label'.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    log.info("Loading '%s' from %s (sheet: %s)", label, filepath, sheet or "all")

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
        entries.extend(_load_sheet(excel_file, sheet_name, label))

    log.info("  Loaded %d requirements as '%s'", len(entries), label)
    return entries


def _load_sheet(excel_file: pd.ExcelFile, sheet_name: str, label: str) -> List[Dict]:
    """Parse a single sheet into requirement dicts."""
    df = excel_file.parse(sheet_name)
    df.columns = df.columns.str.replace(" ", "")

    # Check critical columns exist
    missing = [col for col in ("RequirementID", "ParentID") if col not in df.columns]
    if missing:
        log.warning(
            "Sheet '%s' missing critical columns: %s — skipping", sheet_name, missing
        )
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

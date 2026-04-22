import json
import logging
from pathlib import Path
from typing import Dict

import pandas as pd

from utils.constants import COLUMNS

log = logging.getLogger(__name__)


def export_ancestry_xlsx(tracer, ancestry: Dict, output_path: str) -> None:
    """Export traced ancestry paths to an xlsx file.

    Columns produced:
      - Level -1 (External), Level 0 (<label>), ..., Level N (<label>)
      - TopLevel_Definition  (definition of the closest ancestor in the path)
      - All 18 DOORS schema columns for the leaf requirement
    """
    level_col_names = ["Level -1 (External)"] + [
        f"Level {i} ({label})"
        for i, label in enumerate(tracer.file_hierarchy_order)
    ]

    # Insert TopLevel_Definition just before Definition
    req_columns = []
    for col in COLUMNS:
        if col == "Definition":
            req_columns.append("TopLevel_Definition")
        req_columns.append(col)

    all_columns = level_col_names + req_columns

    rows = []
    for _level_key, reqs in ancestry.items():
        for req_id, path in reqs.items():
            base_req_id = req_id.split(" [path ")[0]
            req_data = tracer.all_requirements.get(base_req_id, {})
            req_obj = req_data.get("Requirement")
            req_dict = req_obj.to_dict() if req_obj else {col: "" for col in COLUMNS}
            req_level = tracer.file_hierarchy.get(
                req_data.get("file_label", ""), -1
            )

            row = {}
            row["Level -1 (External)"] = path.get(-1, "")
            for i, label in enumerate(tracer.file_hierarchy_order):
                row[f"Level {i} ({label})"] = path.get(i, "")

            # TopLevel_Definition: definitions of the closest ancestor(s)
            top_definition = ""
            for lvl in reversed(range(len(tracer.file_hierarchy_order))):
                if lvl in path and lvl != req_level:
                    defs = []
                    for tid in path[lvl].split("\n"):
                        clean_id = tid.replace(" [DELETED]", "").strip()
                        if not clean_id:
                            continue
                        top_req = tracer.all_requirements.get(clean_id, {})
                        top_req_obj = top_req.get("Requirement")
                        if top_req_obj and top_req_obj.definition:
                            defs.append(top_req_obj.definition)
                    top_definition = "\n".join(defs)
                    break

            for col in COLUMNS:
                if col == "Definition":
                    row["TopLevel_Definition"] = top_definition
                row[col] = req_dict.get(col, "")

            rows.append(row)

    df = pd.DataFrame(rows, columns=all_columns)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, sep=";")
    else:
        df.to_excel(output_path, index=False)
    log.info("Ancestry trace exported to '%s' (%d rows)", output_path, len(df))


def write_debug_files(tracer, ancestry: Dict, output_dir: str, stage: str = "") -> None:
    """Write debug JSON files to output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    suffix = f"_{stage}" if stage else ""

    # All requirements
    serialized = {
        req_id: {
            "requirement": data["Requirement"].to_dict(),
            "deleted": data["deleted"],
            "file_label": data["file_label"],
        }
        for req_id, data in tracer.all_requirements.items()
    }
    _write_json(out / f"debug_all_requirements{suffix}.json", serialized)

    # File sources
    _write_json(out / f"debug_file_sources{suffix}.json", tracer.file_sources)

    # Parent-child maps
    _write_json(
        out / f"debug_parent_to_child{suffix}.json",
        {k: sorted(v) for k, v in tracer.parent_to_children.items()},
    )
    _write_json(
        out / f"debug_child_to_parent{suffix}.json",
        {k: sorted(v) for k, v in tracer.child_to_parents.items()},
    )

    # Ancestry
    ancestry_serial = []
    for lvl_or_label in ancestry:
        for req_id in ancestry[lvl_or_label]:
            ancestry_serial.append({
                "level": str(lvl_or_label),
                "req_id": req_id,
                "path": {
                    str(k): v
                    for k, v in ancestry[lvl_or_label][req_id].items()
                },
            })
    _write_json(out / f"debug_ancestry{suffix}.json", ancestry_serial)

    # Coverage: missing-as-key list
    coverage = tracer.verify_coverage(ancestry, stage)
    if coverage["missing_as_key"]:
        lines = []
        for mid in coverage["missing_as_key"]:
            lbl = tracer.all_requirements.get(mid, {}).get("file_label", "?")
            lines.append(f"{mid}  ({lbl})")
        (out / f"debug_missing_as_key{suffix}.txt").write_text("\n".join(lines))

    log.info("Debug files written to %s", out)


def _write_json(path: Path, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

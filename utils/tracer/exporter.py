import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from utils.constants import COLUMNS

log = logging.getLogger(__name__)


def build_ancestry_dataframe(tracer, ancestry: Dict) -> pd.DataFrame:
    """Build the ancestry export DataFrame before writing to disk."""
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
    # Group entries by (level_key, base_req_id) so multi-parent extras collapse
    # into one row.  Each group entry is (via_pid_or_None, path_dict).
    grouped: Dict[Tuple, List] = defaultdict(list)
    for level_key, reqs in ancestry.items():
        for req_id, path in reqs.items():
            via_pid: Optional[str] = None
            if " [via " in req_id:
                via_pid = req_id.split(" [via ")[1].rstrip("]")
            base_req_id = req_id.split(" [via ")[0].split(" [path ")[0]
            grouped[(level_key, base_req_id)].append((via_pid, path))

    for (level_key, base_req_id), entries in grouped.items():
        req_data = tracer.all_requirements.get(base_req_id, {})
        req_obj = req_data.get("Requirement")
        req_dict = req_obj.to_dict() if req_obj else {col: "" for col in COLUMNS}
        req_level = tracer.file_hierarchy.get(req_data.get("file_label", ""), -1)

        # Merge level columns: union of all IDs across every path for this req
        merged_levels: Dict[object, List[str]] = defaultdict(list)
        for _via_pid, path in entries:
            for lvl, ids_str in path.items():
                for v in ids_str.split("\n"):
                    if v and v not in merged_levels[lvl]:
                        merged_levels[lvl].append(v)

        row: Dict = {}
        row["Level -1 (External)"] = "\n".join(merged_levels.get(-1, []))
        for i, label in enumerate(tracer.file_hierarchy_order):
            row[f"Level {i} ({label})"] = "\n".join(merged_levels.get(i, []))

        # TopLevel_Definition: one block per matched parent, each prefixed
        # with [Via parent: PID] when there are multiple parents.
        multi = len(entries) > 1
        top_def_blocks = []
        for via_pid, path in entries:
            # Find closest ancestor level
            anc_def = ""
            for lvl in reversed(range(len(tracer.file_hierarchy_order))):
                if lvl in path and lvl != req_level:
                    defs = []
                    for tid in path[lvl].split("\n"):
                        clean_id = tid.replace(" [DELETED]", "").strip()
                        top_req = tracer.all_requirements.get(clean_id, {})
                        top_req_obj = top_req.get("Requirement")
                        if top_req_obj and top_req_obj.definition:
                            defs.append(tid + ":\n" + top_req_obj.definition)
                    anc_def = "\n\n".join(defs)
                    break

            if multi and via_pid:
                prefix = f"[Via parent: {via_pid}]"
                block = f"{prefix}\n\n{anc_def}" if anc_def else prefix
            else:
                block = anc_def
            if block:
                top_def_blocks.append(block)

        top_definition = "\n\n---\n\n".join(top_def_blocks)

        for col in COLUMNS:
            if col == "Definition":
                row["TopLevel_Definition"] = top_definition
            row[col] = req_dict.get(col, "")

        rows.append(row)

    return pd.DataFrame(rows, columns=all_columns)


def export_ancestry_xlsx(tracer, ancestry: Dict, output_path: str) -> None:
    """Export traced ancestry paths to an xlsx file.

    Columns produced:
      - Level -1 (External), Level 0 (<label>), ..., Level N (<label>)
      - TopLevel_Definition  (definition of the closest ancestor in the path)
      - All 18 DOORS schema columns for the leaf requirement
    """
    df = build_ancestry_dataframe(tracer, ancestry)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if output_path.endswith(".csv"):
        df.to_csv(output_path, index=False, sep=";")
    else:
        df.to_excel(output_path, index=False)
    log.info("Ancestry trace exported to '%s' (%d rows)", output_path, len(df))


def write_debug_files(
    tracer,
    ancestry: Dict,
    output_dir: str,
    stage: str = "",
    coverage: Dict = None,
) -> None:
    """Write debug JSON files to output_dir.

    ``coverage`` should be the dict returned by ``tracer.verify_coverage()``.
    If omitted, the missing-as-key debug file is skipped.
    """
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
    if coverage and coverage["missing_as_key"]:
        lines = []
        for mid in coverage["missing_as_key"]:
            lbl = tracer.all_requirements.get(mid, {}).get("file_label", "?")
            lines.append(f"{mid}  ({lbl})")
        (out / f"debug_missing_as_key{suffix}.txt").write_text("\n".join(lines))

    log.info("Debug files written to %s", out)


def _write_json(path: Path, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

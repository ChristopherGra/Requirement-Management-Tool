import logging
from collections import defaultdict
from typing import Dict, List, Set

log = logging.getLogger(__name__)


class RequirementsTracer:
    """Core tracing engine for parent-child requirement relationships.

    Usage (programmatic — also used by the CLI):
        tracer = RequirementsTracer()
        tracer.add_source(entries)          # from loader.load_requirements()
        tracer.set_hierarchy([...])
        tracer.link_extra(extra_entries)     # optional
        ancestry = tracer.trace()
        ancestry = tracer.filter_redundant(ancestry)
    """

    def __init__(self):
        self.parent_to_children: Dict[str, Set[str]] = defaultdict(set)
        self.child_to_parents: Dict[str, Set[str]] = defaultdict(set)
        self.all_requirements: Dict[str, Dict] = {}
        self.file_sources: Dict[str, str] = {}
        self.file_hierarchy: Dict[str, int] = {}
        self.file_hierarchy_order: List[str] = []
        self.extra_links: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_source(self, entries: List[Dict]) -> int:
        """Ingest loaded requirement dicts. Returns count added."""
        count = 0
        for entry in entries:
            req = entry["requirement"]
            self.all_requirements[req.requirement_id] = {
                "Requirement": req,
                "deleted": entry["deleted"],
                "file_label": entry["label"],
            }
            self.file_sources[req.requirement_id] = entry["label"]
            count += 1
        return count

    def set_hierarchy(self, order: List[str]) -> None:
        """Set file hierarchy from most abstract (index 0) to most derived."""
        self.file_hierarchy = {label: i for i, label in enumerate(order)}
        self.file_hierarchy_order = list(order)
        log.info("Hierarchy set (%d levels):", len(order))
        for i, label in enumerate(order):
            log.info("  [%d] %s", i, label)

    def link_extra(self, entries: List[Dict]) -> None:
        """Add extra-linked requirements that may reference any hierarchy level.

        Call *after* set_hierarchy() and add_source() for all main sources.
        """
        if not entries:
            return
        label = entries[0]["label"]
        self.add_source(entries)
        self.extra_links.append(label)
        next_level = len(self.file_hierarchy_order)
        self.file_hierarchy[label] = next_level
        self.file_hierarchy_order.append(label)
        log.info("Linked extra requirements: %s as level %d", label, next_level)

        for entry in entries:
            req = entry["requirement"]
            self._add_relationship(req.parent_id, req.requirement_id, entry["deleted"])

    def trace(self) -> Dict[str, Dict[str, Dict[int, str]]]:
        """Build relationships bottom-up, then scrape full ancestry.

        Returns ancestry keyed by file label -> req_id -> {level: ids_str}.
        """
        self._build_relationships()
        ancestry = self._scrape_ancestry()
        if self.extra_links:
            ancestry = self._handle_extra_links(ancestry)
        return ancestry

    def filter_redundant(
        self, ancestry: Dict[str, Dict[str, Dict[int, str]]]
    ) -> Dict[int, Dict[str, Dict[int, str]]]:
        """Keep only leaf requirements not already covered as ancestors.

        Returns ancestry keyed by hierarchy level (int) -> req_id -> path.
        """
        filtered: Dict[int, Dict[str, Dict[int, str]]] = defaultdict(dict)
        covered: Set[str] = set()
        for label in self.file_hierarchy_order[::-1]:
            lvl = self.file_hierarchy[label]
            for req_id, level_dict in ancestry.get(label, {}).items():
                covered.update(
                    pid for val in level_dict.values() for pid in val.split("\n")
                )
                if req_id not in covered:
                    filtered[lvl][req_id] = level_dict
        return filtered

    def verify_coverage(self, ancestry: Dict, stage: str = "") -> Dict:
        """Check that every loaded requirement appears in the ancestry output.

        Returns a dict with coverage statistics (useful for programmatic checks).
        """
        ancestry_keys: Set[str] = set()
        ancestry_values: Set[str] = set()

        for _key, reqs in ancestry.items():
            for req_id, path in reqs.items():
                clean_id = req_id.split(" [path ")[0].replace(" [DELETED]", "")
                ancestry_keys.add(clean_id)
                for val_str in path.values():
                    for v in val_str.split("\n"):
                        stripped = v.replace(" [DELETED]", "").strip()
                        if stripped:
                            ancestry_values.add(stripped)

        all_ids = set(self.all_requirements.keys())
        all_ancestry_ids = ancestry_keys | ancestry_values

        missing_as_key = all_ids - ancestry_keys
        missing_entirely = all_ids - all_ancestry_ids
        parent_only = ancestry_values - all_ids

        tag = f" [{stage}]" if stage else ""
        log.info("--- Coverage Check%s ---", tag)
        log.info("  Total loaded requirements: %d", len(all_ids))
        log.info("  Ancestry keys (leaf rows):  %d", len(ancestry_keys))
        log.info("  Ancestry values (in paths): %d", len(ancestry_values))
        log.info("  IDs missing as keys:        %d", len(missing_as_key))
        log.info("  IDs missing entirely:        %d", len(missing_entirely))
        log.info("  Parent-only (not loaded):    %d", len(parent_only))

        if missing_entirely:
            log.warning("  LOST IDs (not in any key or value):")
            for mid in sorted(missing_entirely):
                lbl = self.all_requirements[mid].get("file_label", "?")
                log.warning("      %s  (%s)", mid, lbl)
        else:
            log.info("  All requirement IDs are covered.")

        return {
            "total": len(all_ids),
            "keys": len(ancestry_keys),
            "values": len(ancestry_values),
            "missing_as_key": sorted(missing_as_key),
            "missing_entirely": sorted(missing_entirely),
            "parent_only": sorted(parent_only),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _add_relationship(self, parent_id: str, child_id: str, deleted: str) -> None:
        for p in parent_id.split():
            if not p:
                continue
            if deleted:
                self.parent_to_children[p].add(child_id + " [DELETED]")
                self.child_to_parents[child_id + " [DELETED]"].add(p)
            else:
                self.parent_to_children[p].add(child_id)
                self.child_to_parents[child_id].add(p)

    def _build_relationships(self) -> None:
        """Traverse the hierarchy bottom-up to build parent-child links."""
        for file_label in self.file_hierarchy_order[::-1]:
            if file_label in self.extra_links:
                continue
            relevant = [
                (rid, d)
                for rid, d in self.all_requirements.items()
                if d["file_label"] == file_label
            ]
            log.info(
                "Processing %s (level %d): %d requirements",
                file_label,
                self.file_hierarchy[file_label],
                len(relevant),
            )
            for req_id, data in relevant:
                req = data["Requirement"]
                self._add_relationship(req.parent_id, req_id, data["deleted"])

    def _trace_ancestors(self, req_id: str, is_deleted: bool) -> List[str]:
        """BFS upward from a requirement, returning ancestor IDs."""
        lookup = req_id + " [DELETED]" if is_deleted else req_id
        queue = list(self.child_to_parents.get(lookup, set()))
        path: List[str] = []
        visited: Set[str] = set()
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            cur_data = self.all_requirements.get(current, {})
            cur_deleted = bool(cur_data.get("deleted", ""))
            path.append(current + (" [DELETED]" if cur_deleted else ""))
            cur_lookup = current + " [DELETED]" if cur_deleted else current
            queue.extend(self.child_to_parents.get(cur_lookup, set()))
        return path

    def _group_by_level(self, path: List[str]) -> Dict[int, str]:
        """Group ancestor IDs by their hierarchy level."""
        groups: Dict[int, List[str]] = defaultdict(list)
        for anc_id in path:
            lvl = self.file_hierarchy.get(
                self.all_requirements.get(
                    anc_id.replace(" [DELETED]", ""), {}
                ).get("file_label", ""),
                -1,
            )
            groups[lvl].append(anc_id)
        return {lvl: "\n".join(groups[lvl]) for lvl in sorted(groups, reverse=True)}

    def _scrape_ancestry(self) -> Dict[str, Dict[str, Dict[int, str]]]:
        """Trace each requirement's full ancestry, grouped by hierarchy level."""
        result: Dict[str, Dict[str, Dict[int, str]]] = {}
        for label in self.file_hierarchy_order:
            if label in self.extra_links:
                continue
            log.info("Scraping ancestry for: %s", label)
            level_reqs = sorted(
                (rid, d)
                for rid, d in self.all_requirements.items()
                if d["file_label"] == label
            )
            result[label] = {
                rid: self._group_by_level(
                    self._trace_ancestors(rid, bool(d["deleted"]))
                )
                for rid, d in level_reqs
            }
        return result

    def _handle_extra_links(
        self, ancestry: Dict[str, Dict[str, Dict[int, str]]]
    ) -> Dict[str, Dict[str, Dict[int, str]]]:
        """Integrate extra-linked requirements into the ancestry dict.

        For each extra requirement, search all existing ancestry entries for
        a parent match. When found, copy and extend the matched trace path.
        """
        for label in self.extra_links:
            ancestry[label] = {}
            extra_level = self.file_hierarchy[label]
            log.info(
                "Integrating extra links for: %s (level %d)", label, extra_level
            )

            for req_id, data in self.all_requirements.items():
                if data["file_label"] != label:
                    continue

                parent_ids = set(data["Requirement"].parent_id.split())
                # Filter noise tokens
                parent_ids = {p for p in parent_ids if "created" not in p.lower()}

                deleted = data.get("deleted", "")

                if not parent_ids:
                    ancestry[label][req_id] = {}
                    continue

                matched_paths: Dict[str, Dict[int, List[str]]] = {}
                unmatched_parents: List[str] = []

                for pid in parent_ids:
                    found = False
                    for src_label, src_reqs in ancestry.items():
                        if src_label in self.extra_links:
                            continue
                        for src_req_id, path in src_reqs.items():
                            ids_in_path = {src_req_id.replace(" [DELETED]", "")}
                            for val_str in path.values():
                                ids_in_path.update(
                                    v.replace(" [DELETED]", "")
                                    for v in val_str.split("\n")
                                )
                            if pid not in ids_in_path:
                                continue

                            found = True
                            if pid not in matched_paths:
                                matched_paths[pid] = defaultdict(list)

                            for lvl, val_str in path.items():
                                for v in val_str.split("\n"):
                                    if v not in matched_paths[pid][lvl]:
                                        matched_paths[pid][lvl].append(v)

                            src_data = self.all_requirements.get(src_req_id, {})
                            src_level = self.file_hierarchy.get(
                                src_data.get("file_label", ""), -1
                            )
                            src_deleted = bool(src_data.get("deleted", ""))
                            src_tag = src_req_id + (
                                " [DELETED]" if src_deleted else ""
                            )
                            if src_tag not in matched_paths[pid][src_level]:
                                matched_paths[pid][src_level].append(src_tag)

                    if not found:
                        unmatched_parents.append(pid)

                if matched_paths:
                    for idx, ppath in enumerate(matched_paths.values()):
                        key = req_id if idx == 0 else f"{req_id} [path {idx + 1}]"
                        final_path = {
                            lvl: "\n".join(ids) for lvl, ids in ppath.items()
                        }
                        if unmatched_parents:
                            existing = final_path.get(-1, "")
                            ext_str = "\n".join(unmatched_parents)
                            final_path[-1] = (
                                f"{existing}\n{ext_str}".strip("\n")
                                if existing
                                else ext_str
                            )
                        ancestry[label][key] = final_path
                else:
                    ancestry[label][req_id] = {-1: "\n".join(parent_ids)}

            total = sum(
                1 for d in self.all_requirements.values() if d["file_label"] == label
            )
            log.info(
                "  Integrated %d / %d %s requirements",
                len(ancestry[label]),
                total,
                label,
            )
        return ancestry

"""
Shared constants for requirements processing.
Contains column definitions, mappings, and normalization rules.
"""

# Target column order and names (DOORS-compatible 16-column schema)
COLUMNS = [
    "Parent ID",
    "Requirement ID",
    "Type",
    "Sub-Type",
    "Title",
    "Definition",
    "Notes",
    "Remarks",
    "Responsibility",
    "Applicability",
    "Compliance",
    "Compliance Notes",
    "Verification",
    "Verification Notes",
    "Reference Document",
    "Original ESA Identifier"
]

# Define how incoming columns map to target columns (case-insensitive keys)
COLUMN_MAPPING = {
    "req id": "Requirement ID",
    "requirement id": "Requirement ID",
    "id": "Requirement ID",
    "object identifier": "Requirement ID",
    "object id": "Requirement ID",
    "parent": "Parent ID",
    "parent id": "Parent ID",
    "parent requirement id": "Parent ID",
    "source": "Parent ID",
    "object type": "Type",
    "type": "Type",
    "sub-type": "Sub-Type",
    "subtype": "Sub-Type",
    "title": "Title",
    "definition": "Definition",
    "description": "Definition",
    "req description": "Definition",
    "note": "Notes",
    "notes": "Notes",
    "comments": "Notes",
    "remarks": "Remarks",
    "responsibility": "Responsibility",
    "responsible": "Responsibility",
    "owner": "Responsibility",
    "applicability": "Applicability",
    "applicable": "Applicability",
    "verification": "Verification",
    "verification method": "Verification",
    "compliance": "Compliance",
    "status": "Compliance",
    "compliance status": "Compliance",
    "compliance note": "Compliance Notes",
    "compliance notes": "Compliance Notes",
    "compliance comment": "Compliance Notes",
    "verification note": "Verification Notes",
    "verification notes": "Verification Notes",
    "verification comment": "Verification Notes",
    "reference": "Reference Document",
    "reference document": "Reference Document",
    "ref doc": "Reference Document",
    "document": "Reference Document",
    "original esa identifier": "Original ESA Identifier",
    "orginal esa identifier": "Original ESA Identifier",  # Common typo
    "esa identifier": "Original ESA Identifier",
    "esa id": "Original ESA Identifier",
}

# Compliance normalization mapping
COMPLIANCE_MAP = {
    "compliant": "C",
    "c": "C",
    "non-compliant": "NC",
    "non compliant": "NC",
    "noncompliant": "NC",
    "not-compliant": "NC",
    "not compliant": "NC",
    "notcompliant": "NC",
    "nc": "NC",
    "partially-compliant": "PC",
    "partially compliant": "PC",
    "partial-compliant": "PC",
    "partial compliant": "PC",
    "partially": "PC",
    "partial": "PC",
    "pc": "PC"
}

# PDF keyword mapping (from read_pdf.py)
PDF_KEYWORDS = {
    "ID :": "requirement_id",
    "Object Type :": "type",
    "Source :": "source",
    "Verification Method :": "verification",
    "Compliance :": "compliance",
    "Subsystem Allocation :": "allocation",
    "Justification & Comments :": "comments",
    "Compliance Comment :": "compliance_comment",
    # Add truncated safeguards
    "ompliance Comment :": "compliance_comment",
}

# Debug mode configuration
DEBUG_MODE = False  # Set to True to enable automatic responses
DEBUG_RESPONSES = {
    "sheet_selection": "1",      # Always select first sheet
    "column_mapping": "skip",    # Always skip unmapped columns
}

# Cache configuration
CACHE_DIR = ".cache"
CACHE_FILE = "file_processing_cache.json"

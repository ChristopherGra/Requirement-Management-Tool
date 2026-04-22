"""
Shared constants for requirements processing.
Contains column definitions, mappings, and normalization rules.
"""

# Target column order and names (DOORS-compatible 18-column schema)
COLUMNS = [
    "ParentID",
    "RequirementID",
    "Type",
    "SubType",
    "Title",
    "Definition",
    "Notes",
    "Remarks",
    "Responsibility",
    "SubSysApplicability",
    "Applicability",
    "Compliance",
    "ComplianceNotes",
    "Verification",
    "VerificationNotes",
    "ReferenceDocument",
    "OriginalESAIdentifier",
    "UpdatesMade"
]

# Define how incoming columns map to target columns (case-insensitive keys)
COLUMN_MAPPING = {
    "req id": "RequirementID",
    "requirement id": "RequirementID",
    "id": "RequirementID",
    "object identifier": "RequirementID",
    "object id": "RequirementID",
    "parent": "ParentID",
    "parent id": "ParentID",
    "parent requirement id": "ParentID",
    "source": "ParentID",
    "object type": "Type",
    "type": "Type",
    "sub-type": "SubType",
    "subtype": "SubType",
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
    "subsysapplicability": "SubSysApplicability",
    "subsys applicability": "SubSysApplicability",
    "applicability": "SubSysApplicability",
    "applicable": "SubSysApplicability",
    "verification": "Verification",
    "verification method": "Verification",
    "compliance": "Compliance",
    "status": "Compliance",
    "compliance status": "Compliance",
    "compliance note": "ComplianceNotes",
    "compliance notes": "ComplianceNotes",
    "compliance comment": "ComplianceNotes",
    "verification note": "VerificationNotes",
    "verification notes": "VerificationNotes",
    "verification comment": "VerificationNotes",
    "reference": "ReferenceDocument",
    "reference document": "ReferenceDocument",
    "ref doc": "ReferenceDocument",
    "document": "ReferenceDocument",
    "original esa identifier": "OriginalESAIdentifier",
    "orginal esa identifier": "OriginalESAIdentifier",  # Common typo
    "esa identifier": "OriginalESAIdentifier",
    "esa id": "OriginalESAIdentifier",
    "updates made": "UpdatesMade",
    "updates": "UpdatesMade",
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

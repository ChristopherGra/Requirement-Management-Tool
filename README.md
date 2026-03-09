 # Requirements Management Tool

A modular Python tool that processes requirement documents from various formats (Excel, CSV, PDF) and standardizes them into a unified 17-column DOORS-compatible structure.

## Status

**WIP**

## Important Note About Sample Data

**All content in this repository is generic and fictional.** The requirement documents contain only basic software application requirements created for demonstration purposes. No real project data is included.

## Features

### Core Functionality
- **Multi-Format Support**: Process Excel (.xlsx, .xls, .xlsm), CSV, and PDF files
- **Intelligent Column Mapping**: Automatic mapping with interactive fallback for unmapped columns
- **Smart Caching**: Remembers user choices (sheet selection, column mappings) across sessions
- **Text Normalization**: Unicode normalization and compliance value standardization (C/NC/PC)
- **Batch Processing**: Process entire directories with file type filtering
- **DOORS Integration**: Export to DOORS-compatible CSV (semicolon delimiter) or Excel

## Installation

```bash
# Clone repository
git clone https://github.com/ChristopherGra/Requirement-Management-Tool.git
cd Requirement-Management-Tool

# Create virtual environment
python3 -m venv rm_env
source rm_env/bin/activate  # On Windows: rm_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Process a single file
python3 requirements_processor.py input.xlsx

# Process with custom output
python3 requirements_processor.py input.csv -o output.csv

# Batch process all files in directory
python3 requirements_processor.py --batch requirement_documents/

# Process only PDFs
python3 requirements_processor.py --batch docs/ --type pdf

# Generate DOORS template
python3 requirements_processor.py --template templates/requirements_template.xlsx

# Clear cache (reset user choices)
python3 requirements_processor.py --clear-cache
```

## Architecture

```
RM/
├── requirements_processor.py    # CLI entry point
├── utils/                       # Shared utilities
│   ├── constants.py            # COLUMNS schema, mappings
│   ├── text_processing.py     # Text normalization
│   ├── io_helpers.py           # File I/O & user input
│   ├── cache.py                # FileCache class
│   └── base_processor.py       # BaseProcessor ABC
└── processors/                  # File-type processors
    ├── excel_processor.py      # Excel/CSV handler
    └── pdf_processor.py        # PDF parser
```

## 17-Column DOORS Schema

| Column | Description |
|--------|-------------|
| ParentID | Parent requirement identifier |
| RequirementID | Unique requirement identifier |
| Type | Requirement type (Functional, Non-Functional, etc.) |
| SubType | Requirement sub-classification |
| Title | Short requirement title |
| Definition | Full requirement description |
| Notes | Implementation notes |
| Remarks | Review comments |
| Responsibility | Responsible team/person |
| SubSystemApplicability | Sub-system applicability |
| Applicability | Where requirement applies |
| Compliance | Compliance status (C/NC/PC) |
| ComplianceNotes | Compliance details |
| Verification | Verification method (Test, Review, Demo, etc.) |
| VerificationNotes | Verification details |
| ReferenceDocument | Source document reference |
| OriginalESAIdentifier | Original ESA requirement ID |

## Usage Examples

### Interactive Column Mapping

When the tool encounters unmapped columns, it displays an interactive menu:

```
Column 'req id' could not be automatically mapped.

Available target columns:
  (Dimmed = already assigned)
  1. ParentID              5. Definition            9. Compliance           13. VerificationNotes
  2. RequirementID         6. Notes                10. ComplianceNotes     14. ReferenceDocument
  ...

Enter target column name/number for 'req id' (or 'skip' to ignore): 2
```

Choices are cached - the next time you process the same file, previous mappings are remembered.

### Multi-Sheet Excel Files

For Excel files with multiple sheets:

```
File 'requirements.xlsx' contains multiple sheets:
  1. Overview
  2. Requirements
  3. Test Cases
Please enter the sheet name or number (1-3): 2
```

Sheet selection is also cached for subsequent runs.


## Cache Management

User choices are cached in `.cache/file_processing_cache.json`:
- Sheet selections (for multi-sheet Excel files)
- Column mappings (for interactive mapping)

Cache automatically invalidates when files are modified (mtime/size change).

Manual cache clear: `python3 requirements_processor.py --clear-cache`


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Christopher Granabetter IfA - UVIE  
November 2025

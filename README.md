# Requirements Management Tool

A modular Python project for normalizing requirement documents and tracing parent-child relationships across the normalized outputs. The repository now exposes one cohesive workflow while keeping the normalization and tracer subsystems separately usable.

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
- **Integrated Trace Workflow**: Normalize configured sources first, then run the tracer against the generated normalized files

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
# Unified entry point
python3 requirements_cli.py --help

# Run only normalization
python3 requirements_cli.py manage input.xlsx

# Run only tracing
python3 requirements_cli.py trace --config example.cfg

# Run normalize -> trace as one workflow
python3 requirements_cli.py pipeline --config example.cfg

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
├── requirements_cli.py          # Unified CLI: manage / trace / pipeline
├── requirements_processor.py    # Normalization CLI entry point
├── run_requirements_tracer.py   # Tracer CLI entry point
├── utils/                       # Shared utilities
│   ├── constants.py            # COLUMNS schema, mappings
│   ├── text_processing.py     # Text normalization
│   ├── io_helpers.py           # File I/O & user input
│   ├── cache.py                # FileCache class
│   └── base_processor.py       # BaseProcessor ABC
├── processors/                  # File-type processors
    ├── excel_processor.py      # Excel/CSV handler
    └── pdf_processor.py        # PDF parser
├── reqtracer/                   # Parent-child trace engine
└── workflows/                   # Cross-tool orchestration
  └── trace_pipeline.py       # Normalize-then-trace workflow
```

## Working Modes

The repository now has three intended entry modes:

- `manage`: use only the normalization tool and export DOORS-ready files.
- `trace`: use only the tracing tool against already normalized files.
- `pipeline`: use one config-driven workflow that normalizes each configured source into `output/normalized_for_trace/` and then runs the tracer on those generated files.

The standalone scripts remain valid. The unified CLI exists to make the repository feel like one tool instead of two disconnected ones.

## 18-Column DOORS Schema

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
| UpdatesMade | Record of updates/changes made |

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

## Trace Pipeline

The integrated pipeline reuses the existing tracer `.cfg` file format. For each configured source and extra-link source, it:

1. Normalizes the raw input with the management tool.
2. Writes the normalized intermediate files to a dedicated folder.
3. Generates a reproducible config snapshot for those normalized files.
4. Runs the tracer on the generated normalized inputs.

Example:

```bash
python3 requirements_cli.py pipeline --config example.cfg --output-dir output
```

Generated artifacts:

- `output/normalized_for_trace/*.xlsx`: normalized intermediate files used by tracing
- `output/normalized_for_trace/trace_pipeline.generated.cfg`: generated tracer config referencing those files
- `output/ancestry_trace.xlsx`: final trace export


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Christopher Granabetter IfA - UVIE  
November 2025

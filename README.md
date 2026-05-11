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

### Complete Pipeline
```bash
# Unified entry point
python3 requirements_cli.py --help

# Run only normalization
python3 requirements_cli.py manage input.xlsx

# Run only tracing
python3 requirements_cli.py trace --config output/normalized_for_trace/trace_pipeline.generated.cfg
```

### Requirements Processor (Normalization)
```bash
# Process a single file
python3 requirements_processor.py input.xlsx

# Process with custom output
python3 requirements_processor.py input.csv -o output.csv

# Batch process all files in directory
python3 requirements_processor.py --batch requirement_documents/

# Process only PDFs
python3 requirements_processor.py --batch docs/ --type pdf

# Generate template
python3 requirements_processor.py --template templates/requirements_template.xlsx

# Clear cache (reset user choices)
python3 requirements_processor.py --clear-cache
```

### Requirements Tracer (with normalized files)
```bash
# Run tracer standalone
python3 requirements_tracer.py -c output/normalized_for_trace/trace_pipeline.generated.cfg
python3 requirements_tracer.py -c output/normalized_for_trace/trace_pipeline.generated.cfg -o output/custom/ --debug
```

## Repository Layout

```text
RM/
├── requirements_cli.py              # Unified CLI: manage / trace / pipeline
├── requirements_processor.py        # Normalization CLI entry point
├── requirements_tracer.py           # Tracer CLI entry point
├── compliance_matrix.py             # Splits annotated ancestry back into per-source compliance matrices
├── example.cfg                      # Example tracer configuration
├── utils/
│   ├── base_processor.py            # Shared processor base class + template generation
│   ├── cache.py                     # FileCache implementation
│   ├── constants.py                 # column schema, column mapping, compliance mapping
│   ├── io_helpers.py                # Input/output helpers and prompts
│   ├── text_processing.py           # Text normalization helpers
│   ├── text_similarity_checker.py   # CSV similarity checker
│   ├── eval_similarity.py           # Similarity result evaluation helpers
│   └── tracer/
│       ├── config.py                # .cfg parser and tracer config model
│       ├── loader.py                # Requirement loading for trace inputs
│       ├── tracer.py                # Core ancestry tracing engine
│       ├── exporter.py              # Trace export and debug file writing
│       └── pipeline.py              # Normalize-then-trace orchestration
├── processors/
│   ├── excel_processor.py           # Excel and CSV normalization
│   ├── pdf_processor.py             # Keyword-based PDF normalization
│   └── text_extraction_test.py      # Text Extraction test script
├── requirement_documents/           # Example and project input documents
├── templates/
│   └── requirement_template_gen1.csv
└── output/                          # Generated outputs, normalized intermediates, trace exports
```

## Three Entry Points

### 1. `requirements_cli.py`

Unified entry point for the whole repository.

```bash
python requirements_cli.py manage ...
python requirements_cli.py trace ...
python requirements_cli.py pipeline -c example.cfg
```

Use this when you want one stable command surface for both normalization and tracing.

Subcommands:

| Command | Purpose |
|---------|---------|
| `manage` | Passes arguments through to `requirements_processor.py` |
| `trace` | Passes arguments through to `requirements_tracer.py` |
| `pipeline` | Normalizes configured sources, writes normalized intermediates, then runs the tracer |

Pipeline-specific options:

| Flag | Description |
|------|-------------|
| `-c`, `--config` | Required tracer config file |
| `-o`, `--output-dir` | Override the trace output directory |
| `--normalized-dir` | Override where normalized intermediates are written |
| `--debug` | Force tracer debug file output |
| `--no-filter` | Export all ancestry rows instead of only leaf rows |
| `-v`, `--verbose` | Enable INFO/DEBUG logging |

Examples:

```bash
python requirements_cli.py manage requirement_documents/samples/sample_requirements.csv
python requirements_cli.py trace -c example.cfg --debug
python requirements_cli.py pipeline -c example.cfg --output-dir output --normalized-dir output/normalized_for_trace -v
```

### 2. `requirements_processor.py`

Standalone normalization entry point. Use this when you only need to convert source documents into the standardised schema.

Supported modes:

- Process a single file.
- Process all matching files in a directory.
- Process all sources declared in a tracer `.cfg` file.
- Generate a blank template file.
- Clear cached interactive choices.

Examples:

```bash
# Single file
python requirements_processor.py requirement_documents/samples/sample_requirements.csv

# Custom output path
python requirements_processor.py requirement_documents/samples/sample_requirements.csv -o output/sample_normalized.xlsx

# Batch processing
python requirements_processor.py --batch requirement_documents/samples/
python requirements_processor.py --batch requirement_documents/ --type pdf

# Normalize all sources declared in a config file
python requirements_processor.py -c example.cfg -o output/normalized_from_cfg

# Generate a template
python requirements_processor.py --template templates/requirement_template_gen1.csv

# Clear cache
python requirements_processor.py --clear-cache
```

Standalone processor options:

| Flag | Description |
|------|-------------|
| `input` | Optional single input file |
| `-c`, `--config` | Normalize all sources declared in a `.cfg` file |
| `-o`, `--output` | Output file for single-file mode, or output directory for config mode |
| `--batch` | Process all supported files in a directory |
| `--type` | Filter batch mode by `all`, `pdf`, `excel`, or `csv` |
| `--template` | Generate a blank template file |
| `--clear-cache` | Clear `.cache/file_processing_cache.json` |
| `-v`, `--verbose` | Enable verbose output |

How normalization behaves:

- Excel and CSV files use the Excel processor.
- PDF files use the PDF processor.
- Unmapped columns trigger an interactive mapping prompt.
- Multi-sheet Excel files prompt for a sheet if one is not specified.
- Text is cleaned and compliance values are normalized to `C`, `NC`, or `PC` when possible.
- Outputs preserve the project-standard 18-column order.

### 3. `requirements_tracer.py`

Standalone tracing entry point. Use this when your requirement sources are already prepared for tracing or when you want direct control over trace execution without the normalization step.

Examples:

```bash
python requirements_tracer.py -c example.cfg
python requirements_tracer.py -c example.cfg -o output/custom/
python requirements_tracer.py -c example.cfg --debug
python requirements_tracer.py -c example.cfg --no-filter -v
```

Standalone tracer options:

| Flag | Description |
|------|-------------|
| `-c`, `--config` | Required tracer configuration file |
| `-o`, `--output-dir` | Override the output directory from config |
| `--debug` | Force debug JSON file output |
| `--no-filter` | Skip redundant-ancestry filtering |
| `-v`, `--verbose` | Enable DEBUG-level logging |

## Tracer Configuration Format

The tracer and the pipeline share the same `.cfg` file format. Paths resolve relative to the config file location.

```ini
[general]
output_dir = output
debug = false

[sources]
# label = filepath [:: sheet_name]
Level 1 Req = requirement_documents/Tracing_Examples/Level1Reqs.xlsx
Level 2 Req = requirement_documents/Tracing_Examples/Level2Reqs.xlsx
Level 3 Req = requirement_documents/Tracing_Examples/Level3Reqs.csv

[hierarchy]
# Ordered from most abstract to most derived
order = Level 1 Req, Level 2 Req, Level 3 Req

[extra_links]
# Optional non-linear links matched after the main hierarchy is built
Level 5 Req = requirement_documents/Tracing_Examples/Level5Reqs.xlsx

[export]
ancestry_xlsx = example_ancestry.csv
```

Config rules:

- Each label in `[hierarchy]` must appear in `[sources]`.
- `:: sheet_name` is optional and only applies to spreadsheet sources.
- `[extra_links]` is optional.
- The pipeline rewrites these inputs into a generated config that points at normalized intermediate files.

## Pipeline Mode

`requirements_cli.py pipeline` exists for raw source documents that are not yet normalized.

What it does:

1. Loads the tracer config.
2. Normalizes every source and extra-link input into `output/normalized_for_trace/` by default.
3. Writes `trace_pipeline.generated.cfg` so the run is reproducible.
4. Runs the same tracing engine against the normalized outputs.

Example:

```bash
python requirements_cli.py pipeline -c example.cfg --output-dir output
```

Generated artifacts usually include:

- `output/normalized_for_trace/*_normalized.xlsx`
- `output/normalized_for_trace/trace_pipeline.generated.cfg`
- The final ancestry export named by `[export].ancestry_xlsx`

## Trace Inputs And Behavior

All trace inputs must follow the 18-column standardised schema. Missing columns are added as empty during loading.

Important behaviors:

- `ParentID` may contain space-separated parent identifiers.
- `RequirementID` may contain space-separated identifiers and is split into separate logical entries.
- Rows containing the word `deleted` in most fields are flagged and tagged as deleted in trace output.
- Tracing builds ancestry upward through `child -> parent` relationships and groups ancestors by hierarchy level.
- Extra-link sources are matched into existing ancestry paths after the main hierarchy is built.
- Default output is filtered to leaf requirements unless `--no-filter` is used.

## Trace Outputs

Primary export:

- One row per leaf requirement by default.
- `Level -1 (External)` captures unmatched external parent IDs.
- `Level 0 (<label>)` through `Level N (<label>)` capture ancestry by configured hierarchy level.
- `TopLevel_Definition` captures the nearest ancestor definition available in the path.
- The leaf requirement row also includes the full 18-column standardised payload.

Debug files are written when `debug = true` in the config or when `--debug` is passed:

| File | Contents |
|------|----------|
| `debug_all_requirements_<stage>.json` | All loaded requirements |
| `debug_file_sources_<stage>.json` | Source label assigned to each requirement ID |
| `debug_parent_to_child_<stage>.json` | Forward relationship map |
| `debug_child_to_parent_<stage>.json` | Reverse relationship map |
| `debug_ancestry_<stage>.json` | Full ancestry mapping before or after filter |
| `debug_missing_as_key_<stage>.txt` | IDs present as ancestors but not exported as leaf rows |

`<stage>` is `after_scrape` or `after_filter`.

## 18-Column Standardised Schema

| Column | Description |
|--------|-------------|
| `ParentID` | Parent requirement identifier or identifiers |
| `RequirementID` | Unique requirement identifier |
| `Type` | Requirement type |
| `SubType` | Requirement subtype |
| `Title` | Short title |
| `Definition` | Full requirement text |
| `Notes` | Notes |
| `Remarks` | Remarks |
| `Responsibility` | Responsible owner or team |
| `SubSysApplicability` | Sub-system applicability |
| `Applicability` | Applicability scope |
| `Compliance` | Compliance value, usually `C`, `NC`, or `PC` |
| `ComplianceNotes` | Compliance details |
| `Verification` | Verification method |
| `VerificationNotes` | Verification details |
| `ReferenceDocument` | Source document reference |
| `OriginalESAIdentifier` | Original ESA requirement ID |
| `UpdatesMade` | Manual updates or changes |

## Interactive Features And Cache

Interactive normalization choices are cached in `.cache/file_processing_cache.json`.

Cached values include:

- Selected sheets for multi-sheet Excel files.
- Manual column mappings for partially matched inputs.

Cache invalidation is based on file path, modification time, and size. To clear it manually:

```bash
python requirements_processor.py --clear-cache
```

## Programmatic Usage

Normalization:

```python
from pathlib import Path

from processors import ExcelProcessor
from utils import FileCache

cache = FileCache()
processor = ExcelProcessor(cache)
requirements = processor.extract_requirements(Path("input.xlsx"))
df = processor.requirements_to_dataframe(requirements)
df = processor.normalize_dataframe(df)
processor.export(df, Path("output.csv"))
```

Tracing:

```python
from requirements_tracer import run_trace
from utils.tracer.config import load_config

config = load_config("example.cfg")
run_trace(config, output_dir="output", debug=True, no_filter=False)
```

Pipeline:

```python
from utils.tracer.pipeline import run_normalize_and_trace

run_normalize_and_trace("example.cfg")
```

## Compliance Matrix Script

`compliance_matrix.py` dissects an annotated ancestry output back into per-source normalized compliance matrices.

### Workflow

1. Run the pipeline to produce a combined ancestry export (e.g. `output/example/example_ancestry.csv`).
2. Manually annotate that file in Excel — filling in `Compliance`, `Applicability`, and related columns.
3. Run `compliance_matrix.py` to split the annotated rows back out into one compliance matrix file per configured source.

Output files are written to `<output_dir>/compliance/` and named `<label>_normalized_compliance_matrix.csv` (or `.xlsx`).

### Usage

```bash
# Basic usage — reads ancestry path and output dir from the .cfg file
python compliance_matrix.py -c example.cfg

# Point at a specific annotated ancestry file
python compliance_matrix.py -c example.cfg --ancestry output/example/example_ancestry_annotated.xlsx

# Override where compliance matrices are written
python compliance_matrix.py -c example.cfg --output-dir output/compliance/

# Override the normalized intermediates directory
python compliance_matrix.py -c example.cfg --normalized-dir output/normalized_for_trace/

# Write .xlsx instead of .csv
python compliance_matrix.py -c example.cfg --fmt xlsx
```

Options:

| Flag | Description |
|------|-------------|
| `-c`, `--config` | Required tracer `.cfg` file |
| `--ancestry` | Path to the annotated ancestry file (overrides config default) |
| `--output-dir` | Override the compliance output directory |
| `--normalized-dir` | Override the normalized intermediates directory |
| `--fmt` | Output format: `csv` (default) or `xlsx` |
| `-v`, `--verbose` | Enable DEBUG-level logging |

## Text Similarity Utilities

The repository also includes an early text similarity workflow for comparing requirement CSVs.

```bash
python utils/text_similarity_checker.py text_similarity_input/test_child_requirements.csv text_similarity_input/test_parent_requirements.csv
```

`utils/eval_similarity.py` can then be used to inspect a generated similarity debug CSV.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Author

Christopher Granabetter IfA - UVIE  
April 2026

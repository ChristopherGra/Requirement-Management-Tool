"""
PDF table-based processor for requirements extraction.
Handles structured PDFs where requirements presented as tables.

Usage:
    python -m processors.text_extraction_test                       # uses .env
    python -m processors.text_extraction_test path/to/file.pdf      # explicit path
    python -m processors.text_extraction_test file.pdf -o out.csv   # custom output
"""

import sys
from pathlib import Path
from typing import List

import pymupdf4llm

from utils.base_processor import BaseProcessor, Requirement
from utils.text_processing import normalize_unicode_text, normalize_whitespace
from utils import get_output_path, load_env


class PDFTableProcessor(BaseProcessor):
    """
    Handles PDF requirement extraction using Markdown-table parsing.

    Features:
    - Converts PDF to Markdown via pymupdf4llm
    - Splits table rows into requirement fields
    - Multi-line support via <br> tags
    - Unicode normalization
    """

    def extract_requirements(self, input_path: Path) -> List[Requirement]:
        """
        Extract requirements from a PDF file.

        Args:
            input_path: Path to .pdf file

        Returns:
            List of Requirement objects
        """
        input_path = Path(input_path)

        lines = self._extract_pdf_text(input_path)
        lines = self._reduce_to_requirement_lines(lines)

        requirements = [self._create_requirement_from_line(line) for line in lines]
        return requirements

    def _extract_pdf_text(self, input_path: Path) -> List[str]:
        """
        Extract and normalize text lines from PDF.

        Args:
            input_path: Path to PDF file

        Returns:
            List of cleaned, non-empty text lines
        """
        text = pymupdf4llm.to_markdown(input_path)
        text = normalize_unicode_text(text)

        cleaned_lines = [
            normalize_whitespace(line)
            for line in text.splitlines()
            if line.strip()
        ]
        return cleaned_lines

    def _reduce_to_requirement_lines(self, lines: List[str]) -> List[str]:
        """
        Filter and group table rows into requirement data lines.

        Skips header rows (|ID …) and separator rows (|---|).
        Only keeps rows with exactly 10 pipe-delimited fields.

        Args:
            lines: All text lines from PDF

        Returns:
            List of table-row strings (one per requirement)
        """
        blocks: List[str] = []
        current_block: List[str] = []

        for line in lines:
            if line.startswith("|---|") or not line.startswith("|") or len(line.split("|")) != 10:
                continue

            if line.startswith("|ID"):
                if current_block:
                    blocks.extend(current_block)
                current_block = []
            elif line.startswith("|"):
                current_block.append(line)

        if current_block:
            blocks.extend(current_block)
        return blocks

    def _create_requirement_from_line(self, line: str) -> Requirement:
        """
        Parse a single table row into a Requirement.

        Expected columns (pipe-delimited):
            ID | Parent ID | Title | Description | Verification |
            Subsystem | Justification | Status

        Args:
            line: A Markdown table row

        Returns:
            Populated Requirement object
        """
        line = line.replace("<br>", "\n")
        req_id, parent_id, title, description, verification, subsystem, justification, status = (
            line.split("|")[1:-1]
        )

        return Requirement(
            requirement_id=req_id.strip(),
            parent_id=parent_id.strip(),
            type=title.strip(),
            definition=description.strip(),
            verification=verification.strip(),
            responsibility=subsystem.strip(),
            verification_notes=justification.strip(),
            notes=f"Status: {status.strip()}",
        )


def main() -> None:
    """CLI entry point: process a PDF and export normalised requirements."""
    import argparse

    load_env()

    parser = argparse.ArgumentParser(description="Extract requirements from PDF tables.")
    parser.add_argument("input", nargs="?", help="Path to PDF file (default: $TEST_PDF_PATH from .env)")
    parser.add_argument("-o", "--output", default=None, help="Output CSV path (default: output/<stem>_normalized.csv)")
    args = parser.parse_args()

    # Resolve input path
    import os
    input_file = args.input or os.getenv("TEST_PDF_PATH")
    if not input_file:
        parser.error(
            "No input file specified. Pass a path or set TEST_PDF_PATH in .env\n"
            "  See .env.example for reference."
        )

    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Process
    processor = PDFTableProcessor(cache=None)
    requirements = processor.extract_requirements(input_path)
    print(f"\nExtracted {len(requirements)} requirements")

    df = processor.requirements_to_dataframe(requirements)
    df = processor.normalize_dataframe(df)

    output_path = Path(args.output) if args.output else get_output_path(input_file)
    processor.export(df, output_path)
    print(f"{'-' * 60}\n")


if __name__ == "__main__":
    main()
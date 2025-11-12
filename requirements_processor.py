#!/usr/bin/env python3
"""
Requirements Processor - Unified CLI Tool
==========================================

Normalizes requirements from Excel/CSV/PDF into DOORS-ready format.

Usage:
    python requirements_processor_new.py input.xlsx -o output.csv
    python requirements_processor_new.py --batch archive/ --type pdf
    python requirements_processor_new.py --template output/template.xlsx
    python requirements_processor_new.py --clear-cache
    
Author: Christopher Granabetter Ifa - UVIE
Date: November 2025
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from utils import FileCache, detect_file_type, get_output_path, generate_template
from processors import ExcelProcessor, PDFProcessor


def get_processor(file_path: Path, cache: FileCache):
    """
    Factory function: return appropriate processor for file type.
    
    Args:
        file_path: Path to file
        cache: FileCache instance
        
    Returns:
        ExcelProcessor or PDFProcessor
        
    Raises:
        ValueError: If file type is unsupported
    """
    file_type = detect_file_type(file_path)
    
    if file_type in ['excel', 'csv']:
        return ExcelProcessor(cache)
    elif file_type == 'pdf':
        return PDFProcessor(cache)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def process_single_file(
    input_path: Path,
    output_path: Optional[Path] = None,
    cache: Optional[FileCache] = None
):
    """
    Process a single requirements file.
    
    Args:
        input_path: Path to input file
        output_path: Optional output path (auto-generated if None)
        cache: FileCache instance (created if None)
    """
    if cache is None:
        cache = FileCache()
    
    print(f"\n{'-'*60}")
    print(f"Processing: {input_path.name}")
    print(f"{'-'*60}")
    
    # Get appropriate processor
    try:
        processor = get_processor(input_path, cache)
    except ValueError as e:
        print(f"Error: {e}")
        return False
    
    # Extract requirements
    requirements = processor.extract_requirements(input_path)
    print(f"\nExtracted {len(requirements)} requirements")
    
    # Convert to DataFrame
    df = processor.requirements_to_dataframe(requirements)
    
    # Normalize
    df = processor.normalize_dataframe(df)
    
    # Determine output path
    if output_path is None:
        output_path = get_output_path(input_path)
    
    # Export
    processor.export(df, output_path)
    
    print(f"{'-'*60}\n")
    return True


def process_batch(
    directory: Path,
    file_type_filter: str = 'all',
    cache: Optional[FileCache] = None
):
    """
    Process all files in a directory.
    
    Args:
        directory: Directory containing requirements files
        file_type_filter: 'all', 'pdf', 'excel', or 'csv'
        cache: FileCache instance (created if None)
    """
    if cache is None:
        cache = FileCache()
    
    print(f"\n{'-'*60}")
    print(f"BATCH PROCESSING: {directory}")
    print(f"Filter: {file_type_filter}")
    print(f"{'-'*60}\n")
    
    # Supported extensions
    extensions = {
        'all': ['.pdf', '.xlsx', '.xls', '.xlsm', '.csv'],
        'pdf': ['.pdf'],
        'excel': ['.xlsx', '.xls', '.xlsm'],
        'csv': ['.csv'],
    }
    
    allowed_exts = extensions.get(file_type_filter, extensions['all'])
    
    # Find all matching files
    files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in allowed_exts
    ]
    
    if not files:
        print(f"No {file_type_filter} files found in {directory}")
        return
    
    print(f"Found {len(files)} file(s) to process\n")
    
    # Process each file
    success_count = 0
    for file_path in files:
        try:
            if process_single_file(file_path, cache=cache):
                success_count += 1
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            continue
    
    print(f"BATCH COMPLETE: {success_count}/{len(files)} files processed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Process requirements from Excel/CSV/PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single PDF file
  %(prog)s requirement_documents/sample.pdf
  
  # Process Excel file with custom output
  %(prog)s archive/requirements.xlsx -o output/normalized.csv
  
  # Process all files in a directory
  %(prog)s --batch requirement_documents/
  
  # Process only PDFs in a directory
  %(prog)s --batch requirement_documents/ --type pdf
  
  # Generate a template file
  %(prog)s --template output/template.xlsx
  
  # Clear the file processing cache
  %(prog)s --clear-cache
        """
    )
    
    # Main argument: input file or batch directory
    parser.add_argument(
        'input',
        nargs='?',
        type=Path,
        help='Input file path (or use --batch for directory processing)'
    )
    
    # Output path
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file path (default: output/<filename>_normalized.csv)'
    )
    
    # Batch processing
    parser.add_argument(
        '--batch',
        type=Path,
        help='Process all files in directory'
    )
    
    # File type filter for batch processing
    parser.add_argument(
        '--type',
        choices=['all', 'pdf', 'excel', 'csv'],
        default='all',
        help='Type of files to process in batch mode (default: all)'
    )
    
    # Template generation
    parser.add_argument(
        '--template',
        type=Path,
        help='Generate a blank template file'
    )
    
    # Cache management
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear the file processing cache'
    )
    
    # Verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize cache
    cache = FileCache()
    
    # Handle cache clearing
    if args.clear_cache:
        cache.clear()
        print("Cache cleared successfully")
        return 0
    
    # Handle template generation
    if args.template:
        print(f"Generating template: {args.template}")
        generate_template(args.template)
        return 0
    
    # Handle batch processing
    if args.batch:
        if not args.batch.is_dir():
            print(f"Error: {args.batch} is not a directory")
            return 1
        
        process_batch(args.batch, args.type, cache)
        return 0
    
    # Handle single file processing
    if args.input:
        if not args.input.exists():
            print(f"Error: {args.input} does not exist")
            return 1
        
        if not args.input.is_file():
            print(f"Error: {args.input} is not a file")
            return 1
        
        success = process_single_file(args.input, args.output, cache)
        return 0 if success else 1
    
    # No action specified
    parser.print_help()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

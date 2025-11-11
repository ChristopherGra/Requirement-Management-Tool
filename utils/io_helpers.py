"""
I/O helper utilities for interactive prompts and file operations.
"""

import os
from pathlib import Path
from utils.constants import DEBUG_MODE, DEBUG_RESPONSES


def debug_input(prompt, debug_key=None):
    """
    Testable input function that supports debug mode.
    
    In DEBUG_MODE, returns predefined responses instead of prompting user.
    This allows automated testing without user interaction.
    
    Args:
        prompt: The prompt to display to the user
        debug_key: Key to lookup in DEBUG_RESPONSES for automated response
        
    Returns:
        User input string or debug response
        
    Example:
        >>> DEBUG_MODE = True
        >>> DEBUG_RESPONSES = {"test": "auto_response"}
        >>> debug_input("Enter value: ", "test")
        "auto_response"
    """
    if DEBUG_MODE and debug_key and debug_key in DEBUG_RESPONSES:
        response = DEBUG_RESPONSES[debug_key]
        print(f"{prompt}{response}  [DEBUG MODE]")
        return response
    else:
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled by user.")
            return None


def list_directory(path):
    """
    List all relevant files in the given directory.
    
    Filters out placeholders, markdown files, and temporary files.
    
    Args:
        path: Directory path to list
        
    Returns:
        List of file paths, or empty list if error
    """
    try:
        files = os.listdir(path)
        return [
            os.path.join(path, file) 
            for file in files 
            if file != ".placeholder" 
            and not file.endswith(".md") 
            and not file.startswith('~')
            and not file.startswith('.')
        ]
    except Exception as e:
        print(f"Error accessing directory '{path}': {e}")
        return []


def detect_file_type(file_path):
    """
    Detect the type of requirements file based on extension.
    
    Args:
        file_path: Path to file (str or Path object)
        
    Returns:
        String: 'excel', 'csv', 'pdf', or 'unknown'
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext in ['.xlsx', '.xls', '.xlsm']:
        return 'excel'
    elif ext == '.csv':
        return 'csv'
    elif ext == '.pdf':
        return 'pdf'
    else:
        return 'unknown'


def ensure_directory_exists(directory_path):
    """
    Create directory if it doesn't exist.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path object of created/existing directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(input_path, output_dir='output', suffix='_normalized'):
    """
    Generate appropriate output path for processed file.
    
    Args:
        input_path: Input file path
        output_dir: Output directory (default: 'output')
        suffix: Suffix to add to filename (default: '_normalized')
        
    Returns:
        Path object for output file
    """
    input_file = Path(input_path)
    output_directory = ensure_directory_exists(output_dir)
    output_name = f"{input_file.stem}{suffix}.csv"
    return output_directory / output_name

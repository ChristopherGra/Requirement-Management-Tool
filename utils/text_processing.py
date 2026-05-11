"""
Text processing utilities for requirements normalization.
Handles Unicode normalization, cell cleaning, and text formatting.
"""

import unicodedata
import re


def normalize_unicode_text(text):
    """
    Normalize Unicode text to ASCII-friendly characters.
    
    Uses NFKD normalization to convert compatibility characters to simpler forms,
    then manually replaces math symbols and typography that can't be auto-converted.
    
    Args:
        text: Input text with Unicode characters
        
    Returns:
        Normalized text with ASCII characters
    """
    if not isinstance(text, str):
        return str(text)

    # Manual replacements for math symbols and typography — must run BEFORE
    # the ASCII encode step so these characters are not silently stripped.
    replacements = {
        '\u2264': '<=',  # ≤ less than or equal
        '\u2265': '>=',  # ≥ greater than or equal
        '\u2260': '!=',  # ≠ not equal
        '\u00b1': '+-',  # ± plus-minus
        '\u00d7': 'x',   # × multiplication
        '\u00f7': '/',   # ÷ division
        '\u2212': '-',   # − minus sign (different from hyphen)
        '\u2013': '-',   # – en dash
        '\u2014': '--',  # — em dash
        '\u2018': "'",   # ' left single quote
        '\u2019': "'",   # ' right single quote
        '\u201c': '"',   # " left double quote
        '\u201d': '"',   # " right double quote
        '\u2022': '*',   # • bullet point
        '\u00a0': ' ',   # non-breaking space
    }
    
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)

    # NFKD normalization converts compatibility characters to simpler forms,
    # then drop anything still non-ASCII (accented chars etc.).
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')

    return text


def clean_cell_value(value):
    """
    Clean a single cell value for consistent processing.
    
    Converts to string, strips whitespace, normalizes Unicode.
    Optional: remove quotes and convert line breaks.
    
    Args:
        value: Cell value from DataFrame
        
    Returns:
        Cleaned string value
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN check
        return ""
    
    # Convert to string and strip whitespace
    text = str(value).strip()
    
    # Normalize Unicode characters
    text = normalize_unicode_text(text)

    # Replace _x000D_ with actual line breaks
    text = text.replace('_x000D_', '')
    
    return text


def normalize_whitespace(text):
    """
    Normalize whitespace in text (collapse multiple spaces, trim).
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    return re.sub(r'\s+', ' ', text.strip())


def truncate_keyword(text, keyword_map):
    """
    Handle truncated keywords by checking for partial matches.
    
    Used in PDF parsing where keywords may be split across lines.
    Example: "Compliance Comment :" might appear as "ompliance Comment :"
    
    Args:
        text: Line of text to check
        keyword_map: Dictionary of keywords to field names
        
    Returns:
        Tuple of (matched_keyword, field_name) or (None, None)
    """
    for keyword, field in keyword_map.items():
        if keyword in text:
            return keyword, field
    return None, None

def reformat_itemize_in_text(text: str) -> str:
    """Find and reformat all \\begin{itemize}...\\end{itemize} blocks in a text string."""
    blocks = _extract_itemize_blocks(text)
    for block in blocks:
        text = text.replace(block, _reformat_itemize_block(block) + "\n")
    return text

def _extract_itemize_blocks(text: str) -> list[str]:
    """Extract all top-level \\begin{itemize}...\\end{itemize} blocks, handling nesting."""
    results = []
    depth = 0
    start = -1

    for m in re.finditer(r'\\(begin|end){itemize}', text):
        if m.group(1) == 'begin':
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start != -1:
                results.append(text[start:m.end()])
                start = -1

    return results

def _reformat_itemize_block(block: str) -> str:
    """Reformat a single \\begin{itemize}...\\end{itemize} block with proper indentation."""
    
    block = block.replace('\\begin{itemize}', '\n\\begin{itemize}')
    block = block.replace('\\end{itemize}', '\n\\end{itemize}')
    block = block.replace('\\item', '\n\\item')

    depth = 0
    new_lines = []
    for line in block.splitlines():
        if line.startswith('\\begin{itemize}'):
            new_line = "  " * depth + line.strip()
            depth += 1
        elif line.startswith('\\end{itemize}'):
            depth -= 1
            new_line = "  " * depth + line.strip()
        else:
            new_line = "  " * depth + line.strip()
        
        new_lines.append(new_line)
            
        block = "\n".join(new_lines)
    return block

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

    # NFKD normalization converts compatibility characters to simpler forms
    text = unicodedata.normalize('NFKD', text)
    
    # Encode to ASCII, ignoring characters that can't be represented
    # This handles most accented characters automatically
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Manual replacements for math symbols and typography
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

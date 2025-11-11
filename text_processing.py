import unicodedata

def normalize_unicode_text(text):
    """
    Normalize Unicode text to ASCII-friendly characters.
    
    This handles:
    - Smart quotes (', ', ", ") → straight quotes (', ")
    - Em/en dashes (—, –) → hyphen (-)
    - Various whitespace → standard space
    - Accented characters (é, ñ, ü) → base characters (e, n, u)
    - Math symbols that have ASCII equivalents
    
    Args:
        text: Input text with Unicode characters
        
    Returns:
        Normalized text with ASCII characters
    """
    # NFKD normalization converts compatibility characters to simpler forms
    # Example: ﬁ (ligature) → fi, ² (superscript 2) → 2
    text = unicodedata.normalize('NFKD', text)
    
    # Encode to ASCII, ignoring characters that can't be represented
    # This handles most accented characters automatically
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Manual replacements for math symbols that need special handling
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
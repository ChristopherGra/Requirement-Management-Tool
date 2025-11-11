"""
Utilities package for requirements processing.
Shared constants, text processing, caching, and I/O helpers.
"""

from .constants import (
    COLUMNS,
    COLUMN_MAPPING,
    COMPLIANCE_MAP,
    PDF_KEYWORDS,
    DEBUG_MODE,
    DEBUG_RESPONSES,
)
from .text_processing import (
    normalize_unicode_text,
    clean_cell_value,
    normalize_whitespace,
)
from .cache import FileCache
from .io_helpers import (
    debug_input,
    detect_file_type,
    get_output_path,
)
from .base_processor import (
    Requirement,
    BaseProcessor,
    generate_template,
)

__all__ = [
    # Constants
    'COLUMNS',
    'COLUMN_MAPPING',
    'COMPLIANCE_MAP',
    'PDF_KEYWORDS',
    'DEBUG_MODE',
    'DEBUG_RESPONSES',
    # Text processing
    'normalize_unicode_text',
    'clean_cell_value',
    'normalize_whitespace',
    # Cache
    'FileCache',
    # I/O helpers
    'debug_input',
    'detect_file_type',
    'get_output_path',
    # Base classes
    'Requirement',
    'BaseProcessor',
    'generate_template',
]

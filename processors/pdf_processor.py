"""
PDF processor for requirements extraction.
Handles .pdf files with keyword-based parsing.
"""

from pathlib import Path
from typing import List

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf  # Fallback

from utils.base_processor import BaseProcessor, Requirement
from utils.constants import PDF_KEYWORDS
from utils.text_processing import normalize_unicode_text, normalize_whitespace


class PDFProcessor(BaseProcessor):
    """
    Handles PDF requirement extraction using keyword-based parsing.
    
    Features:
    - Extracts structured requirements from formatted PDFs
    - Keyword recognition with truncation handling
    - Multi-line field continuation
    - Unicode normalization
    """
    
    # Keywords that trigger requirement block parsing
    KEYWORDS = PDF_KEYWORDS
    
    def extract_requirements(self, input_path: Path) -> List[Requirement]:
        """
        Extract requirements from PDF file.
        
        Args:
            input_path: Path to .pdf file
            
        Returns:
            List of Requirement objects
        """
        input_path = Path(input_path)
        
        # Extract text from PDF
        lines = self._extract_pdf_text(input_path)
        
        # Group lines into requirement blocks
        blocks = self._group_requirement_blocks(lines)
        
        # Parse each block into a Requirement
        requirements = [self._parse_requirement_block(block) for block in blocks]
        
        return requirements
    
    def _extract_pdf_text(self, input_path: Path) -> List[str]:
        """
        Extract and normalize text lines from PDF.
        
        Args:
            input_path: Path to PDF file
            
        Returns:
            List of text lines (cleaned and normalized)
        """
        doc = pymupdf.open(str(input_path))
        all_lines = []
        
        for page in doc:
            text = page.get_text()
            
            # Normalize Unicode characters
            text = normalize_unicode_text(text)
            
            # Skip header (first 120 chars) and split into lines
            lines = text[120:].split("\n")
            
            # Clean each line: collapse whitespace, strip, filter empty
            cleaned_lines = [
                normalize_whitespace(line)
                for line in lines
                if line.strip()
            ]
            
            all_lines.extend(cleaned_lines)
        
        doc.close()
        return all_lines
    
    def _group_requirement_blocks(self, lines: List[str]) -> List[List[str]]:
        """
        Group lines into requirement blocks.
        
        Each block starts with "ID :" and ends with "Compliance Comment :".
        
        Args:
            lines: All text lines from PDF
            
        Returns:
            List of requirement blocks (each block is a list of lines)
        """
        blocks = []
        current_block = []
        recording = False
        
        for line in lines:
            if line.startswith("ID :"):
                # Start new requirement block
                recording = True
                current_block = [line]
            elif recording:
                current_block.append(line)
                
                # End of requirement block
                if line.startswith("Compliance Comment :") or "ompliance Comment :" in line:
                    blocks.append(current_block)
                    recording = False
                    current_block = []
        
        return blocks
    
    def _parse_requirement_block(self, block: List[str]) -> Requirement:
        """
        Parse a single requirement block into a Requirement object.
        
        Args:
            block: Lines of text for one requirement
            
        Returns:
            Requirement object with extracted fields
        """
        # Initialize all fields as a dictionary
        fields = {
            "requirement_id": "",
            "type": "",
            "definition": "",
            "source": "",
            "verification": "",
            "compliance": "",
            "allocation": "",
            "comments": "",
            "compliance_comment": ""
        }
        
        # Track multi-line field continuation
        current_multiline_field = None
        
        for line in block:
            line_has_keyword = False
            
            # Check each keyword
            for keyword, field in self.KEYWORDS.items():
                if keyword in line:
                    value = line.replace(keyword, '').strip()
                    fields[field] = value
                    
                    # Set multi-line continuation flags
                    if field == "type":
                        current_multiline_field = "definition"
                    elif field == "comments":
                        current_multiline_field = "comments"
                    else:
                        current_multiline_field = None
                    
                    line_has_keyword = True
                    break
            
            # Handle multi-line continuation
            if not line_has_keyword and current_multiline_field:
                fields[current_multiline_field] += " " + line
        
        # Create Requirement (map PDF fields to DOORS schema)
        req = Requirement(
            requirement_id=fields["requirement_id"],
            parent_id=fields["source"],
            type=fields["type"],
            definition=fields["definition"].strip(),
            verification=fields["verification"],
            compliance=fields["compliance"],
            compliance_notes=fields["compliance_comment"].strip(),
            notes=fields["comments"].strip(),
            responsibility=fields["allocation"],
        )
        
        return req

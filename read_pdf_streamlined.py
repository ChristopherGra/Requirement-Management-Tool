"""
Streamlined PDF Requirements Extractor

A refactored version of read_pdf.py with    def extract_text_lines(self) -> List[str]:
        \"\"\"Extract and clean text lines from all PDF pages.\"\"\"
        all_lines = []
        
        for page in self.doc:
            text = page.get_text()  # pyright: ignore[reportAttributeAccessIssue]
            
            # Skip header content (first 120 chars) and clean whitespace
            cleaned_lines = [
                re.sub(r'\\s+', ' ', line.strip()) 
                for line in text[120:].split(\"\\n\") 
                if line.strip()
            ]
            all_lines.extend(cleaned_lines)
        
        return all_linesinability, 
type hints, and object-oriented design.
"""

import pandas as pd
import pymupdf
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Requirement:
    """Data class representing a single requirement with all its attributes."""
    
    id: Optional[str] = None
    object_type: Optional[str] = None
    definition: str = ""
    source: Optional[str] = None
    verification: Optional[str] = None
    compliance: Optional[str] = None
    allocation: Optional[str] = None
    comments: str = ""
    compliance_comment: Optional[str] = None
    
    def __post_init__(self):
        """Clean up text fields after initialization."""
        self.definition = self.definition.strip()
        self.comments = self.comments.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary for DataFrame export."""
        return {
            "ID": self.id,
            "Type": self.object_type,
            "Definition": self.definition,
            "Source": self.source,
            "Verification": self.verification,
            "Compliance": self.compliance,
            "Allocation": self.allocation,
            "Comments": self.comments,
            "Compliance Comment": self.compliance_comment
        }


class PDFRequirementExtractor:
    """Extracts requirements from structured PDF documents."""
    
    # Mapping of keywords to their corresponding field names
    KEYWORD_MAPPINGS = {
        "ID :": "id",
        "Object Type :": "object_type", 
        "Source :": "source",
        "Verification Method :": "verification",
        "Compliance :": "compliance",
        "Subsystem Allocation :": "allocation",
        "Justification & Comments :": "comments",
        "Compliance Comment :": "compliance_comment",
        "ompliance Comment :": "compliance_comment"  # Handle truncated version
    }
    
    # Keywords that trigger text collection for the next lines
    DEFINITION_TRIGGER = "Object Type :"
    COMMENTS_TRIGGER = "Justification & Comments :"
    
    def __init__(self, pdf_path: str):
        """Initialize the extractor with a PDF file path."""
        self.pdf_path = Path(pdf_path)
        self.doc = pymupdf.open(str(pdf_path))
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the document."""
        if hasattr(self, 'doc') and self.doc:
            self.doc.close()
    
    def extract_text_lines(self) -> List[str]:
        """Extract and clean text lines from all PDF pages."""
        all_lines = []
        
        for page in self.doc:
            text = page.get_text()  # pyright: ignore[reportAttributeAccessIssue]
            
            # Skip header content (first 120 chars) and clean whitespace
            cleaned_lines = [
                re.sub(r'\s+', ' ', line.strip()) 
                for line in text[120:].split("\n") 
                if line.strip()
            ]
            all_lines.extend(cleaned_lines)
        
        return all_lines
    
    def group_requirement_blocks(self, lines: List[str]) -> List[List[str]]:
        """Group text lines into individual requirement blocks."""
        requirement_blocks = []
        current_block = []
        is_recording = False
        
        for line in lines:
            if line.startswith("ID :"):
                # Start new requirement block
                if current_block:  # Save previous block if exists
                    requirement_blocks.append(current_block)
                current_block = [line]
                is_recording = True
                
            elif is_recording:
                current_block.append(line)
                
                # End of requirement block
                if line.startswith("Compliance Comment :") or line.startswith("ompliance Comment :"):
                    requirement_blocks.append(current_block)
                    current_block = []
                    is_recording = False
        
        # Don't forget the last block if it exists
        if current_block:
            requirement_blocks.append(current_block)
        
        return requirement_blocks
    
    def parse_requirement_block(self, block: List[str]) -> Requirement:
        """Parse a single requirement block into a Requirement object."""
        field_values = {}
        definition_lines = []
        comments_lines = []
        
        is_collecting_definition = False
        is_collecting_comments = False
        
        for line in block:
            keyword_matched = False
            
            # Check if line starts with any keyword
            for keyword, field_name in self.KEYWORD_MAPPINGS.items():
                if line.startswith(keyword):
                    keyword_matched = True
                    value = line.replace(keyword, "").strip()
                    
                    # Handle N/A values
                    field_values[field_name] = None if value == "N/A" else value
                    
                    # Update collection flags
                    is_collecting_definition = (keyword == self.DEFINITION_TRIGGER)
                    is_collecting_comments = (keyword == self.COMMENTS_TRIGGER)
                    
                    # If there's content on the same line as the keyword, start the collection
                    if value and is_collecting_definition:
                        definition_lines.append(value)
                    elif value and is_collecting_comments:
                        comments_lines.append(value)
                    
                    break
            
            # Collect multi-line content if no keyword was matched
            if not keyword_matched:
                if is_collecting_definition:
                    definition_lines.append(line)
                elif is_collecting_comments:
                    comments_lines.append(line)
        
        # Join collected multi-line content
        if definition_lines:
            field_values["definition"] = " ".join(definition_lines)
        if comments_lines:
            field_values["comments"] = " ".join(comments_lines)
        
        return Requirement(**field_values)
    
    def extract_requirements(self, debug_id: Optional[str] = None, 
                           verbose: bool = True) -> List[Requirement]:
        """
        Extract all requirements from the PDF.
        
        Args:
            debug_id: If provided, pause execution when this requirement ID is found
            verbose: Whether to print extraction progress
            
        Returns:
            List of extracted Requirement objects
        """
        lines = self.extract_text_lines()
        blocks = self.group_requirement_blocks(lines)
        requirements = []
        
        for i, block in enumerate(blocks, 1):
            req = self.parse_requirement_block(block)
            

            
            if verbose:
                print(f"[{i}/{len(blocks)}] Extracted: {req.id}")
            
            # Debug breakpoint
            if debug_id and req.id == debug_id:
                print(f"\n=== DEBUG: Found {debug_id} ===")
                print(f"Raw block: {block}")
                print(f"Parsed Comments: '{req.comments}'")
                print(f"Parsed Compliance Comment: '{req.compliance_comment}'")
                input(f"Pausing for debug at requirement {debug_id}. Press Enter to continue...")
            
            requirements.append(req)
        
        return requirements


def export_to_excel(requirements: List[Requirement], output_path: str) -> None:
    """Export requirements to Excel or CSV file using pandas."""
    if not requirements:
        print("No requirements to export.")
        return
    
    data = [req.to_dict() for req in requirements]
    df = pd.DataFrame(data)
    
    if output_path.endswith('.csv'):
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)
    
    print(f"Successfully exported {len(requirements)} requirements to '{output_path}'")


def main():
    """Main function to extract requirements and export to Excel."""
    # Configuration
    pdf_path = "requirement_documents/sample_requirements_specification.pdf"
    output_path = "output/extracted_requirements_streamlined.csv"
    debug_id = None  # Set to None to disable debug pausing
    
    try:
        # Extract requirements using context manager
        with PDFRequirementExtractor(pdf_path) as extractor:
            print(f"Extracting requirements from: {pdf_path}")
            requirements = extractor.extract_requirements(
                debug_id=debug_id, 
                verbose=True
            )
        
        # Export to file
        export_to_excel(requirements, output_path)
        
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
    except Exception as e:
        print(f"Error during extraction: {e}")
        raise


if __name__ == "__main__":
    main()
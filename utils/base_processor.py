"""
Base classes for requirement processors.
Defines common interface and shared logic for all processor types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional
import pandas as pd
import csv

from utils.constants import COLUMNS, COMPLIANCE_MAP
from utils.text_processing import normalize_unicode_text, clean_cell_value


@dataclass
class Requirement:
    """
    Unified requirement model matching DOORS 16-column schema.
    
    All processors convert their inputs to this common format.
    """
    requirement_id: str = ""
    parent_id: str = ""
    type: str = ""
    sub_type: str = ""
    title: str = ""
    definition: str = ""
    notes: str = ""
    remarks: str = ""
    responsibility: str = ""
    applicability: str = ""
    compliance: str = ""
    compliance_notes: str = ""
    verification: str = ""
    verification_notes: str = ""
    reference_document: str = ""
    original_esa_identifier: str = ""
    
    def to_dict(self):
        """Convert to dictionary with proper column names."""
        return {
            "Parent ID": self.parent_id,
            "Requirement ID": self.requirement_id,
            "Type": self.type,
            "Sub-Type": self.sub_type,
            "Title": self.title,
            "Definition": self.definition,
            "Notes": self.notes,
            "Remarks": self.remarks,
            "Responsibility": self.responsibility,
            "Applicability": self.applicability,
            "Compliance": self.compliance,
            "Compliance Notes": self.compliance_notes,
            "Verification": self.verification,
            "Verification Notes": self.verification_notes,
            "Reference Document": self.reference_document,
            "Original ESA Identifier": self.original_esa_identifier,
        }


class BaseProcessor(ABC):
    """
    Abstract base class for all requirement processors.
    
    Defines common interface and shared normalization logic.
    Subclasses implement file-type-specific extraction.
    """
    
    def __init__(self, cache=None):
        """
        Initialize processor.
        
        Args:
            cache: FileCache instance for storing user choices
        """
        self.cache = cache
    
    @abstractmethod
    def extract_requirements(self, input_path: Path) -> List[Requirement]:
        """
        Extract requirements from source file.
        
        Must be implemented by subclasses.
        
        Args:
            input_path: Path to input file
            
        Returns:
            List of Requirement objects
        """
        pass
    
    def requirements_to_dataframe(self, requirements: List[Requirement]) -> pd.DataFrame:
        """
        Convert list of Requirements to DataFrame.
        
        Args:
            requirements: List of Requirement objects
            
        Returns:
            DataFrame with COLUMNS schema
        """
        if not requirements:
            return pd.DataFrame(columns=COLUMNS)
            
        data = [req.to_dict() for req in requirements]
        df = pd.DataFrame(data)
        
        # Ensure all columns exist in correct order
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
                
        return df[COLUMNS]
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply standard normalization to DataFrame.
        
        - Clean text
        - Normalize compliance values
        - Ensure column order
        
        Args:
            df: Input DataFrame
            
        Returns:
            Normalized DataFrame
        """
        # Clean all text columns
        for col in df.columns:
            if col in COLUMNS:
                df[col] = df[col].apply(clean_cell_value)
        
        # Normalize compliance values
        if 'Compliance' in df.columns:
            df['Compliance'] = df['Compliance'].apply(self._normalize_compliance)
        
        # Ensure column order
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
                
        return df[COLUMNS]
    
    def _normalize_compliance(self, value):
        """
        Normalize compliance status to C/NC/PC.
        
        Args:
            value: Raw compliance value
            
        Returns:
            Normalized compliance code or original if not recognized
        """
        if not value or value == "":
            return ""
            
        value_lower = str(value).strip().lower()
        return COMPLIANCE_MAP.get(value_lower, value)
    
    def export_csv(self, df: pd.DataFrame, output_path: Path):
        """
        Export DataFrame to CSV with semicolon delimiter.
        
        Uses semicolon separator and backslash escaping per project standards.
        
        Args:
            df: DataFrame to export
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(
            output_path,
            sep=';',
            index=False,
            quoting=csv.QUOTE_NONE,
            escapechar='\\'
        )
        print(f"Saved to {output_path}")
    
    def export_excel(self, df: pd.DataFrame, output_path: Path):
        """
        Export DataFrame to Excel file.
        
        Args:
            df: DataFrame to export
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_excel(output_path, index=False)
        print(f"Saved to {output_path}")
    
    def export(self, df: pd.DataFrame, output_path: Path):
        """
        Auto-detect export format from extension and export.
        
        Args:
            df: DataFrame to export
            output_path: Output file path (.csv or .xlsx)
        """
        output_path = Path(output_path)
        ext = output_path.suffix.lower()
        
        if ext == '.csv':
            self.export_csv(df, output_path)
        elif ext in ['.xlsx', '.xls']:
            self.export_excel(df, output_path)
        else:
            # Default to CSV
            self.export_csv(df, output_path.with_suffix('.csv'))


def generate_template(output_path: Path):
    """
    Generate a blank template file with target columns.
    
    Creates a sample row showing expected data format.
    
    Args:
        output_path: Path for template file (.csv or .xlsx)
    """
    df = pd.DataFrame(columns=COLUMNS)
    
    # Add one sample row to show structure
    sample_row = {
        "Parent ID": "REQ-001",
        "Requirement ID": "REQ-001-01",
        "Type": "Functional",
        "Sub-Type": "Performance",
        "Title": "Sample Requirement Title",
        "Definition": "The system shall perform X within Y timeframe.",
        "Notes": "Additional implementation notes",
        "Remarks": "Review comments",
        "Responsibility": "Engineering Team",
        "Applicability": "All subsystems",
        "Compliance": "C",
        "Compliance Notes": "Fully compliant",
        "Verification": "Test",
        "Verification Notes": "Verified by unit test",
        "Reference Document": "REF-DOC-001",
        "Original ESA Identifier": "ESA-REQ-001",
    }
    df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)
    
    # Export using BaseProcessor
    processor = BaseProcessor.__new__(BaseProcessor)  # Create instance without __init__
    processor.cache = None
    processor.export(df, output_path)
    print(f"Template generated: {output_path}")

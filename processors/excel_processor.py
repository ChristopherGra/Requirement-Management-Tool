"""
Excel/CSV processor for requirements extraction.
Handles .xlsx, .xls, .xlsm, and .csv files with interactive column mapping.
"""

import os
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Union

from utils.base_processor import BaseProcessor, Requirement
from utils.constants import COLUMNS, COLUMN_MAPPING
from utils.text_processing import clean_cell_value
from utils.io_helpers import debug_input


class ExcelProcessor(BaseProcessor):
    """
    Handles Excel and CSV files with interactive column mapping.
    
    Features:
    - Multi-sheet Excel file support with caching
    - Automatic column mapping via COLUMN_MAPPING
    - Interactive mapping for unmapped columns
    - Column assignment tracking (prevents duplicates)
    - Cache previous user choices
    """
    
    def extract_requirements(self, input_path: Path) -> List[Requirement]:
        """
        Extract requirements from Excel/CSV file.
        
        Args:
            input_path: Path to .xlsx, .xls, .xlsm, or .csv file
            
        Returns:
            List of Requirement objects
        """
        input_path = Path(input_path)
        
        # Load DataFrame with sheet selection if needed
        df = self._load_spreadsheet(input_path)
        
        if df is None:
            return []
        
        # Standardize column names
        df = self._standardize_columns(df)
        
        # Map columns to target schema
        df = self._map_columns(df, input_path)
        
        # Convert to Requirements
        return self._dataframe_to_requirements(df)
    
    def _load_spreadsheet(self, input_path: Path) -> Union[pd.DataFrame, None]:
        """
        Load spreadsheet with multi-sheet handling.
        
        Args:
            input_path: Path to file
            
        Returns:
            DataFrame or None if unsupported type
        """
        ext = input_path.suffix.lower()
        
        if ext in [".xls", ".xlsx", ".xlsm"]:
            result = self._load_excel_with_sheet_selection(input_path)
            return result if result is not None else pd.DataFrame()
        elif ext == ".csv":
            return pd.read_csv(input_path, encoding="utf-8")
        else:
            print(f"Unsupported file type: {ext}")
            return pd.DataFrame()
    
    def _load_excel_with_sheet_selection(self, input_path: Path) -> Optional[pd.DataFrame]:
        """
        Load Excel file with interactive sheet selection if multiple sheets.
        
        Uses cache to remember previous selection.
        
        Args:
            input_path: Path to Excel file
            
        Returns:
            DataFrame from selected sheet or None if cancelled
        """
        excel_file = pd.ExcelFile(input_path)
        sheet_names : List[str] = [str(name) for name in excel_file.sheet_names]
        
        if len(sheet_names) == 1:
            # Only one sheet, read directly
            return pd.read_excel(input_path)
        
        # Multiple sheets - check cache first
        cached_choices = self.cache.get_choices(str(input_path)) if self.cache else {}
        
        if 'sheet_name' in cached_choices and cached_choices['sheet_name'] in sheet_names:
            selected_sheet = cached_choices['sheet_name']
            print(f"\nUsing cached sheet selection: '{selected_sheet}' [from cache]")
        else:
            selected_sheet = self._prompt_for_sheet(input_path, sheet_names)
            
            # Save sheet selection to cache
            if self.cache and selected_sheet:
                self.cache.save_choices(str(input_path), sheet_name=selected_sheet)
        
        if not selected_sheet:
            return None
            
        print(f"Reading sheet: '{selected_sheet}'")
        return pd.read_excel(input_path, sheet_name=selected_sheet)
    
    def _prompt_for_sheet(self, input_path: Path, sheet_names: List[str]) -> Optional[str]:
        """
        Prompt user to select a sheet from multiple options.
        
        Args:
            input_path: File path (for display)
            sheet_names: List of available sheet names
            
        Returns:
            Selected sheet name or None if cancelled
        """
        print(f"\nFile '{input_path.name}' contains multiple sheets:")
        for i, sheet in enumerate(sheet_names, 1):
            print(f"  {i}. {sheet}")
        
        while True:
            try:
                choice_raw = debug_input(
                    f"Please enter the sheet name or number (1-{len(sheet_names)}): ",
                    "sheet_selection"
                )
                
                if choice_raw is None:  # User cancelled (Ctrl+C returns None from debug_input)
                    return None
                    
                choice = choice_raw.strip()
                
                if not choice:
                    continue
                
                # Check if user entered a number
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(sheet_names):
                        return sheet_names[choice_num - 1]
                    else:
                        print(f"Please enter a number between 1 and {len(sheet_names)}")
                        continue
                
                # Check if user entered a sheet name
                elif choice in sheet_names:
                    return choice
                else:
                    print(f"Sheet '{choice}' not found. Available sheets: {', '.join(sheet_names)}")
                    continue
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                return None
            except Exception as e:
                print(f"Invalid input: {e}")
                continue
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names: lowercase, strip, remove quotes.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized column names
        """
        df.columns = [c.strip().lower().replace('"', '') for c in df.columns]
        return df
    
    def _map_columns(self, df: pd.DataFrame, input_path: Path) -> pd.DataFrame:
        """
        Map source columns to target COLUMNS schema.
        
        Uses automatic mapping first, then interactive for unmapped columns.
        
        Args:
            df: DataFrame with source columns
            input_path: File path (for caching)
            
        Returns:
            DataFrame with target columns
        """
        mapped_df = pd.DataFrame(columns=COLUMNS)
        unmapped_columns = []
        assigned_targets = {}  # Track which targets are already assigned
        
        # Load cached column mappings
        cached_choices = self.cache.get_choices(str(input_path)) if self.cache else {}
        cached_mappings = cached_choices.get('column_mappings', {})
        
        # First pass: automatic mapping
        for src_col in df.columns:
            if src_col in COLUMN_MAPPING:
                tgt_col = COLUMN_MAPPING[src_col]
                print(f"Mapping column '{src_col}' to '{tgt_col}'")
                mapped_df[tgt_col] = df[src_col].apply(clean_cell_value)
                assigned_targets[tgt_col] = src_col
            else:
                unmapped_columns.append(src_col)
        
        # Second pass: handle unmapped columns
        if unmapped_columns:
            print(f"\nFound {len(unmapped_columns)} unmapped column(s):")
            for col in unmapped_columns:
                print(f"  - '{col}'")
            
            user_column_mappings = {}
            
            for src_col in unmapped_columns:
                # Check cache first
                if src_col in cached_mappings:
                    cached_target = cached_mappings[src_col]
                    if cached_target == 'skip' or cached_target == '':
                        print(f"\nUsing cached choice for '{src_col}': skip [from cache]")
                        user_column_mappings[src_col] = 'skip'
                        continue
                    elif cached_target in COLUMNS:
                        print(f"\nUsing cached mapping for '{src_col}' --> '{cached_target}' [from cache]")
                        mapped_df[cached_target] = df[src_col].apply(clean_cell_value)
                        user_column_mappings[src_col] = cached_target
                        assigned_targets[cached_target] = src_col
                        continue
                
                # Interactive mapping
                target_col, should_skip = self._display_column_mapping_menu(
                    src_col, 
                    assigned_targets
                )
                
                if should_skip:
                    user_column_mappings[src_col] = 'skip'
                else:
                    mapped_df[target_col] = df[src_col].apply(clean_cell_value)
                    user_column_mappings[src_col] = target_col
                    assigned_targets[target_col] = src_col
            
            # Save mappings to cache
            if self.cache and user_column_mappings:
                self.cache.save_choices(str(input_path), column_mappings=user_column_mappings)
            
            mapped_count = len(df.columns) - len(unmapped_columns)
            print(f"\nMapping Summary: {mapped_count} columns mapped automatically, "
                  f"{len(unmapped_columns)} columns processed interactively")
        else:
            print("All columns were successfully mapped automatically.")
        
        # Ensure all target columns exist
        for col in COLUMNS:
            if col not in mapped_df.columns:
                mapped_df[col] = ""
        
        # Reorder to match COLUMNS
        return mapped_df[COLUMNS]
    
    def _display_column_mapping_menu(
        self, 
        source_column: str, 
        already_mapped: dict
    ) -> Tuple[Optional[str], bool]:
        """
        Display interactive menu for mapping a source column.
        
        Shows 4-column grid with already-assigned columns dimmed.
        
        Args:
            source_column: The source column name being mapped
            already_mapped: Dict of {target_col: source_col} for assigned columns
            
        Returns:
            Tuple of (chosen_target_column, skip_flag)
        """
        # ANSI color codes
        RESET = '\033[0m'
        DIM = '\033[2m'
        
        print(f"\nColumn '{source_column}' could not be automatically mapped.")
        print(f"\nAvailable target columns:")
        print(f"  {DIM}(Dimmed = already assigned){RESET}")
        
        # Display columns in 4-column grid
        cols_per_row = 4
        for row_idx in range(0, cols_per_row):
            row_items = []
            for col_idx in range(0, len(COLUMNS), cols_per_row):
                if row_idx + col_idx < len(COLUMNS):
                    col_num = row_idx + col_idx + 1
                    col_name = COLUMNS[row_idx + col_idx]
                    
                    # Dim if already mapped
                    if col_name in already_mapped:
                        item = f"{DIM}{col_num:2d}. {col_name:<20}{RESET}"
                    else:
                        item = f"{col_num:2d}. {col_name:<20}"
                    
                    row_items.append(item)
            
            print("  " + " ".join(row_items))
        
        # Show current mappings
        if already_mapped:
            print(f"\n  {DIM}Current mappings:{RESET}")
            for target, source in sorted(already_mapped.items()):
                print(f"    {DIM}'{source}' --> '{target}'{RESET}")
        
        # Get user choice
        while True:
            try:
                choice_raw = debug_input(
                    f"\nEnter target column name/number for '{source_column}' (or 'skip' to ignore): ",
                    "column_mapping"
                )
                
                if choice_raw is None:  # Cancelled
                    return None, True
                    
                choice = choice_raw.strip()
                
                if not choice:
                    continue
                
                # Handle skip
                if choice.lower() == 'skip':
                    print(f"Skipping column '{source_column}'")
                    return None, True
                
                # Handle numeric choice
                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(COLUMNS):
                        tgt_col = COLUMNS[choice_num - 1]
                        
                        # Warn if already mapped
                        if tgt_col in already_mapped:
                            print(f"  {DIM}Warning:{RESET} '{tgt_col}' is already mapped from '{already_mapped[tgt_col]}'")
                            confirm_raw = debug_input("  Overwrite? (y/n): ", "column_mapping")
                            if confirm_raw is None or confirm_raw.strip().lower() != 'y':
                                continue
                        
                        print(f"Mapping column '{source_column}' → '{tgt_col}'")
                        return tgt_col, False
                    else:
                        print(f"Please enter a number between 1 and {len(COLUMNS)}")
                        continue
                
                # Handle name choice
                elif choice in COLUMNS:
                    tgt_col = choice
                    
                    # Warn if already mapped
                    if tgt_col in already_mapped:
                        print(f"  {DIM}Warning:{RESET} '{tgt_col}' is already mapped from '{already_mapped[tgt_col]}'")
                        confirm_raw = debug_input("  Overwrite? (y/n): ", "column_mapping")
                        if confirm_raw is None or confirm_raw.strip().lower() != 'y':
                            continue
                    
                    print(f"Mapping column '{source_column}' → '{tgt_col}'")
                    return tgt_col, False
                else:
                    print(f"Column '{choice}' not found. Available columns: {', '.join(COLUMNS)}")
                    continue
                    
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                return None, True
    
    def _dataframe_to_requirements(self, df: pd.DataFrame) -> List[Requirement]:
        """
        Convert normalized DataFrame to list of Requirement objects.
        
        Args:
            df: DataFrame with COLUMNS schema
            
        Returns:
            List of Requirement objects
        """
        requirements = []
        
        for _, row in df.iterrows():
            req = Requirement(
                requirement_id=row.get("Requirement ID", ""),
                parent_id=row.get("Parent ID", ""),
                type=row.get("Type", ""),
                sub_type=row.get("Sub-Type", ""),
                title=row.get("Title", ""),
                definition=row.get("Definition", ""),
                notes=row.get("Notes", ""),
                remarks=row.get("Remarks", ""),
                responsibility=row.get("Responsibility", ""),
                applicability=row.get("Applicability", ""),
                compliance=row.get("Compliance", ""),
                compliance_notes=row.get("Compliance Notes", ""),
                verification=row.get("Verification", ""),
                verification_notes=row.get("Verification Notes", ""),
                reference_document=row.get("Reference Document", ""),
                original_esa_identifier=row.get("Original ESA Identifier", ""),
            )
            requirements.append(req)
        
        return requirements

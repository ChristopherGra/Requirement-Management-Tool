import os
import pandas as pd
import csv
import json
import hashlib
from pathlib import Path

# Debug mode configuration
DEBUG_MODE = False  # Set to True to enable automatic responses
DEBUG_RESPONSES = {
    "sheet_selection": "1",      # Always select first sheet
    "column_mapping": "skip",    # Always skip unmapped columns
}

# Cache configuration
CACHE_DIR = ".cache"
CACHE_FILE = os.path.join(CACHE_DIR, "file_processing_cache.json")

# column order and names
COLUMNS = [
    "Parent ID",
    "Requirement ID",
    "Type",
    "Sub-Type",
    "Title",
    "Definition",
    "Notes",
    "Remarks",
    "Responsibility",
    "Applicability",
    "Compliance",
    "Compliance Notes",
    "Verification",
    "Verification Notes",
    "Reference Document",
    "Original ESA Identifier"
]

# Define how incoming columns map to target columns (case-insensitive)
COLUMN_MAPPING = {
    "req id": "Requirement ID",
    "requirement id": "Requirement ID",
    "id": "Requirement ID",
    "object identifier": "Requirement ID",
    "object id": "Requirement ID",
    "parent": "Parent ID",
    "parent id": "Parent ID",
    "parent requirement id": "Parent ID",
    "source": "Parent ID",
    "object type": "Type",
    "type": "Type",
    "sub-type": "Sub-Type",
    "subtype": "Sub-Type",
    "title": "Title",
    "definition": "Definition",
    "description": "Definition",
    "req description": "Definition",
    "note": "Notes",
    "notes": "Notes",
    "comments": "Notes",
    "remarks": "Remarks",
    "responsibility": "Responsibility",
    "responsible": "Responsibility",
    "owner": "Responsibility",
    "applicability": "Applicability",
    "applicable": "Applicability",
    "verification": "Verification",
    "verification method": "Verification",
    "compliance": "Compliance",
    "status": "Compliance",
    "compliance status": "Compliance",
    "compliance note": "Compliance Notes",
    "compliance notes": "Compliance Notes",
    "compliance comment": "Compliance Notes",
    "verification note": "Verification Notes",
    "verification notes": "Verification Notes",
    "verification comment": "Verification Notes",
    "reference": "Reference Document",
    "reference document": "Reference Document",
    "ref doc": "Reference Document",
    "document": "Reference Document",
    "original esa identifier": "Original ESA Identifier",
    "orginal esa identifier": "Original ESA Identifier",
    "esa identifier": "Original ESA Identifier",
    "esa id": "Original ESA Identifier",
}

# Compliance normalization
COMPLIANCE_MAP = {
    "compliant": "C",
    "c": "C",
    "non-compliant": "NC",
    "non compliant": "NC",
    "noncompliant": "NC",
    "not-compliant": "NC",
    "not compliant": "NC",
    "notcompliant": "NC",
    "nc": "NC",
    "partially-compliant": "PC",
    "partially compliant": "PC",
    "partial-compliant": "PC",
    "partial compliant": "PC",
    "partially": "PC",
    "partial": "PC",
    "pc": "PC"
}

def generate_template(path):
    """Generate a blank template file with target columns."""
    df = pd.DataFrame(columns=COLUMNS)
    df.at[0, "Parent ID"] = "R-MIS-INST-0001"
    df.at[0, "Requirement ID"] = "R-MIS-INST-ASW-0001"
    df.at[0, "Type"] = "Requirement"
    df.at[0, "Sub-Type"] = "Template Requirement"
    df.at[0, "Title"] = "Sample Requirement"
    df.at[0, "Definition"] = "This is a sample requirement definition."
    df.at[0, "Notes"] = "Additional notes for the requirement."
    df.at[0, "Remarks"] = "To be reviewed by Univie"
    df.at[0, "Responsibility"] = "UVIE"
    df.at[0, "Applicability"] = "Y/N"
    df.at[0, "Compliance"] = "NC/PC/C"
    df.at[0, "Compliance Notes"] = ""
    df.at[0, "Verification"] = "D/A/T/I"
    df.at[0, "Verification Notes"] = ""
    df.at[0, "Reference Document"] = "RD1"
    df.at[0, "Original ESA Identifier"] = "R-MIS-GEN-0001"

    if path.endswith(".csv"):
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False)

    print(f"Template file created at {path}")

def list_directory(path):
    """List all files in the given directory."""
    try:
        files = os.listdir(path)
        return [os.path.join(path, file) for file in files if file != ".placeholder" and not file.endswith(".md") and not file.startswith('~')]
    except Exception as e:
        print(f"Error accessing directory '{path}': {e}")
        return []

def get_file_hash(file_path):
    """Generate a hash of the file to uniquely identify it."""
    # Use file path and modification time for uniqueness
    stat = os.stat(file_path)
    unique_string = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def load_cache():
    """Load the processing cache from disk."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load cache: {e}")
        return {}

def save_cache(cache):
    """Save the processing cache to disk."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def get_cached_choices(file_path):
    """Get cached user choices for a file."""
    cache = load_cache()
    file_hash = get_file_hash(file_path)
    return cache.get(file_hash, {})

def save_user_choices(file_path, sheet_name=None, column_mappings=None):
    """Save user choices for a file to the cache."""
    cache = load_cache()
    file_hash = get_file_hash(file_path)
    
    choices = cache.get(file_hash, {})
    if sheet_name is not None:
        choices['sheet_name'] = sheet_name
    if column_mappings is not None:
        choices['column_mappings'] = column_mappings
    
    cache[file_hash] = choices
    save_cache(cache)

def debug_input(prompt, debug_key=None, fallback_response=""):
    """Helper function for input that can be overridden in debug mode."""
    if DEBUG_MODE and debug_key and debug_key in DEBUG_RESPONSES:
        response = DEBUG_RESPONSES[debug_key]
        print(f"{prompt}{response}  [DEBUG MODE]")
        return response
    else:
        return input(prompt)

def process_column_data(series):
    """Process column data by converting to string, stripping whitespace, and removing quotes."""
    return (
        series
        .astype(str)
        .str.strip()
        .str.replace('"', '', regex=False) 
    )

def normalize_file(input_path):
    ext = os.path.splitext(input_path)[1].lower()
    
    # Load cached choices for this file
    cached_choices = get_cached_choices(input_path)
    selected_sheet = None
    
    if ext in [".xls", ".xlsx", ".xlsm"]:
        # Check if file has multiple sheets
        excel_file = pd.ExcelFile(input_path)
        sheet_names = excel_file.sheet_names
        
        if len(sheet_names) > 1:
            # Check if we have a cached sheet selection
            if 'sheet_name' in cached_choices and cached_choices['sheet_name'] in sheet_names:
                selected_sheet = cached_choices['sheet_name']
                print(f"\nUsing cached sheet selection: '{selected_sheet}' [from cache]")
            else:
                print(f"\nFile '{os.path.basename(input_path)}' contains multiple sheets:")
                for i, sheet in enumerate(sheet_names, 1):
                    print(f"  {i}. {sheet}")
                
                while True:
                    try:
                        choice = debug_input(f"Please enter the sheet name or number (1-{len(sheet_names)}): ", "sheet_selection").strip()
                        
                        # Check if user entered a number
                        if choice.isdigit():
                            choice_num = int(choice)
                            if 1 <= choice_num <= len(sheet_names):
                                selected_sheet = sheet_names[choice_num - 1]
                                break
                            else:
                                print(f"Please enter a number between 1 and {len(sheet_names)}")
                                continue
                        
                        # Check if user entered a sheet name
                        elif choice in sheet_names:
                            selected_sheet = choice
                            break
                        else:
                            print(f"Sheet '{choice}' not found. Available sheets: {', '.join(map(str, sheet_names))}")
                            continue
                            
                    except KeyboardInterrupt:
                        print("\nOperation cancelled by user.")
                        return None
                    except Exception as e:
                        print(f"Invalid input: {e}")
                        continue
                
                # Save the sheet selection to cache
                save_user_choices(input_path, sheet_name=selected_sheet)
            
            print(f"Reading sheet: '{selected_sheet}'")
            df = pd.read_excel(input_path, sheet_name=selected_sheet)
        else:
            # Only one sheet, read it directly
            df = pd.read_excel(input_path)
            
    elif ext == ".csv":
        df = pd.read_csv(input_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Standardize column names (lowercase)
    df.columns = [c.strip().lower().replace("\"", "") for c in df.columns]

    # Map incoming columns to target columns
    mapped_df = pd.DataFrame(columns=COLUMNS)
    unmapped_columns = []
    user_column_mappings = {}
    
    # Load cached column mappings
    cached_mappings = cached_choices.get('column_mappings', {})
    
    for i, src_col in enumerate(df.columns):
        df.iloc[:, i] = df.iloc[:, i]
        if src_col in COLUMN_MAPPING:
            tgt_col = COLUMN_MAPPING[src_col]
            print(f"Mapping column '{src_col}' to '{tgt_col}'")
            mapped_df[tgt_col] = process_column_data(df[src_col])
            
            if tgt_col == "Definition":
                print(mapped_df[tgt_col])

        else:
            unmapped_columns.append(src_col)
    
    # Handle unmapped columns interactively
    if unmapped_columns:
        print(f"\nFound {len(unmapped_columns)} unmapped column(s):")
        for col in unmapped_columns:
            print(f"  - '{col}'")
        
        for src_col in unmapped_columns:
            # Check if we have a cached mapping for this column
            if src_col in cached_mappings:
                cached_target = cached_mappings[src_col]
                if cached_target == 'skip' or cached_target == '':
                    print(f"\nUsing cached choice for '{src_col}': skip [from cache]")
                    user_column_mappings[src_col] = 'skip'
                    continue
                elif cached_target in COLUMNS:
                    print(f"\nUsing cached mapping for '{src_col}' --> '{cached_target}' [from cache]")
                    mapped_df[cached_target] = process_column_data(df[src_col])
                    user_column_mappings[src_col] = cached_target
                    continue
            
            print(f"\nColumn '{src_col}' could not be automatically mapped.")
            
            while True:
                try:
                    print(f"\nAvailable target columns:")
                    # Display columns in 4 columns for compact view
                    cols_per_row = 4
                    for i in range(0, cols_per_row):
                        row_items = []
                        for j in range(0, len(COLUMNS), cols_per_row):
                            if i + j < len(COLUMNS):
                                col_num = i + j + 1
                                col_name = COLUMNS[i + j]
                                row_items.append(f"{col_num:2d}. {col_name:<20}")
                        print("  " + " ".join(row_items))

                    choice = debug_input(f"\nEnter target column name/number for '{src_col}' (or 'skip' to ignore): ", "column_mapping").strip()
                    
                    if choice.lower() == 'skip' or choice == '':
                        print(f"Skipping column '{src_col}'")
                        user_column_mappings[src_col] = 'skip'
                        break
                    
                    # Check if user entered a number
                    elif choice.isdigit():
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(COLUMNS):
                            tgt_col = COLUMNS[choice_num - 1]
                            print(f"Mapping column '{src_col}' to '{tgt_col}'")
                            mapped_df[tgt_col] = process_column_data(df[src_col])
                            user_column_mappings[src_col] = tgt_col
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(COLUMNS)}")
                            continue
                    
                    # Check if user entered a target column name
                    elif choice in COLUMNS:
                        tgt_col = choice
                        print(f"Mapping column '{src_col}' to '{tgt_col}'")
                        mapped_df[tgt_col] = process_column_data(df[src_col])
                        user_column_mappings[src_col] = tgt_col
                        break
                    else:
                        print(f"Column '{choice}' not found. Available columns: {', '.join(COLUMNS)}")
                        continue
                        
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user.")
                    return None
                except Exception as e:
                    print(f"Invalid input: {e}")
                    continue
        
        # Save the new column mappings to cache
        if user_column_mappings:
            save_user_choices(input_path, column_mappings=user_column_mappings)
        
        mapped_count = len(df.columns) - len(unmapped_columns)
        print(f"\nMapping Summary: {mapped_count} columns mapped automatically, {len(unmapped_columns)} columns processed interactively")
    else:
        print("All columns were successfully mapped automatically.")
    
    # Ensure all target columns exist (fill missing)
    for col in COLUMNS:
        if col not in mapped_df.columns:
            mapped_df[col] = ""

    # Normalize compliance status
    def normalize_compliance(val):
        if pd.isna(val):
            return ""
        val = str(val).strip().lower()
        return COMPLIANCE_MAP.get(val, val)  # fallback to original if unknown

    mapped_df["Compliance"] = mapped_df["Compliance"].apply(normalize_compliance)

    # Reorder columns exactly
    mapped_df = mapped_df[COLUMNS]

    return mapped_df

def save_to_file(df, path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xls", ".xlsx", ".xlsm"]:
        df.to_excel(path, index=False)
    elif ext == ".csv":
        df.to_csv(path, index=False, quoting=csv.QUOTE_NONE, escapechar='\\', sep=';')
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    print(f"File saved to {path}")

if __name__ == "__main__":
    # Enable debug mode for automatic responses (no user input required)
    #DEBUG_MODE = True  # Uncomment this line to enable debug mode
    
    #generate_template("requirement_template_gen1.csv")
    
    dfs = []
    for file in list_directory("archive"):
        print(f"\nProcessing file: {file}")
        dfs.append(normalize_file(file))
        
        save_to_file(dfs[-1], os.path.join("output", os.path.basename(file.replace(" ", "_").split('.')[0] + "_normalized.csv")))
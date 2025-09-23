import os
import pandas as pd
import csv

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
    "Reference Document"
]

# Define how incoming columns map to target columns (case-insensitive)
COLUMN_MAPPING = {
    "req id": "Requirement ID",
    "requirement id": "Requirement ID",
    "id": "Requirement ID",
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
    "verification": "Verification",
    "compliance": "Compliance",
    "status": "Compliance",
    "compliance status": "Compliance",
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

    if path.endswith(".csv"):
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False)

    print(f"Template file created at {path}")

def normalize_file(input_path, output_path):
    ext = os.path.splitext(input_path)[1].lower()
    if ext in [".xls", ".xlsx", ".xlsm"]:
        df = pd.read_excel(input_path)
    elif ext == ".csv":
        df = pd.read_csv(input_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Standardize column names (lowercase)
    df.columns = [c.strip().lower().replace("\"", "") for c in df.columns]

    # Map incoming columns to target columns
    mapped_df = pd.DataFrame(columns=COLUMNS)
    unmapped = 0
    for i, src_col in enumerate(df.columns):
        df.iloc[:, i] = df.iloc[:, i]
        if src_col in COLUMN_MAPPING:
            tgt_col = COLUMN_MAPPING[src_col]
            print(f"Mapping column '{src_col}' to '{tgt_col}'")
            mapped_df[tgt_col] = (
                                    df[src_col]
                                    .astype(str)                          # make sure it’s string
                                    .str.strip()                          # trim whitespace
                                    .str.replace('"', '', regex=False)    # remove quotes
                                 )
            
            if tgt_col == "Definition":
                print(mapped_df[tgt_col])

        else:
            print(f"Ignoring unmapped column '{src_col}'")
            unmapped += 1

    if unmapped > 0:
        print(f"Warning: {unmapped} unmapped columns were ignored.")
        print(f"{len(df.columns)-unmapped} columns out of {len(df.columns)} were mapped.")
    else:
        print("All columns were successfully mapped.")
    
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

    # Save to CSV
    mapped_df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONE, escapechar='\\', sep=';')
    print(f"Normalized file saved to {output_path}")

    #print(mapped_df["Definition"])

if __name__ == "__main__":
    input_file = "archive/WIMU.xlsx"
    #generate_template("requirement_template_gen1.csv")

    normalize_file(input_file, "normalized_requirements.csv")
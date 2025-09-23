import pandas as pd

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


if __name__ == "__main__":
    generate_template("requirement_template_gen1.csv")
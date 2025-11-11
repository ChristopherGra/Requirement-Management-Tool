import pandas as pd
import pymupdf # imports the pymupdf library
import re
import os
import unicodedata

class Requirement:
  def __init__(self, id, object_type, definition, source, verification, compliance, allocation, comments, compliance_comment):
    self.id = id
    self.type = object_type
    self.definition = definition
    self.source = source
    self.verification = verification
    self.compliance = compliance
    self.allocation = allocation
    self.comments = comments
    self.compliance_comment = compliance_comment

KEYWORDS = [
    "ID :",
    "Object Type :",
    "Source :",
    "Verification Method :",
    "Compliance :",
    "Subsystem Allocation :",
    "Justification & Comments :",
    "Compliance Comment :"
]


def export_requirements_to_excel(requirements, output_path):
    """
    Export a list of Requirement objects to an Excel file using pandas.
    Args:
        requirements (list of Requirement): The requirements to export.
        output_path (str): Path to the output Excel file.
    """
    data = []
    for req in requirements:
        data.append({
            "ID": req.id,
            "Type": req.type,
            "Definition": req.definition,
            "Source": req.source,
            "Verification": req.verification,
            "Compliance": req.compliance,
            "Allocation": req.allocation,
            "Comments": req.comments,
            "Compliance Comment": req.compliance_comment
        })
    df = pd.DataFrame(data)
    if output_path.endswith('.csv'):
        df.to_csv(output_path, index=False, sep=';')
    else:
        df.to_excel(output_path, index=False)

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

def list_directory(path):
    """List all files in the given directory."""
    try:
        files = os.listdir(path)
        return [os.path.join(path, file) for file in files if file != ".placeholder" and not file.endswith(".md")]
    except Exception as e:
        print(f"Error accessing directory '{path}': {e}")
        return []
    

directory_path = "requirement_documents"

files = [file for file in list_directory(directory_path) if file.endswith('.pdf')]

for file in files:
    requirements_document = pymupdf.open(file)

    complete_doc_split = []
    for page in requirements_document:
        text = str(page.get_text())
        
        # Normalize Unicode characters to ASCII equivalents
        text = normalize_unicode_text(text)
        
        page_split = [re.sub(r'\s+', ' ', item.strip()) for item in text[120:].split("\n") if item.strip() != '']
        print(page_split)
        complete_doc_split.extend(page_split)

    record_req = False
    all_reqs = []
    for line in complete_doc_split:
        if line.startswith("ID :"):
            record_req = True
            single_req = []

        if record_req:
            single_req.append(line)

        if line.startswith("Compliance Comment :"):
            all_reqs.append(single_req)
            record_req = False


    requirements = []
    for req in all_reqs:

        req_id = None
        object_type = None
        definition = None
        source = None
        verification = None
        compliance = None
        allocation = None
        comments = None
        compliance_comment = None

        definition_next = False
        justification_next = False
        definition = ""
        comments = ""
        for line in req:
            print(line)
            for key in KEYWORDS:
                line_has_keyword = False
                if line.startswith(key):
                    definition_next = False
                    justification_next = False
                    value = line.replace(key, "").strip()
                    
                    if value == "N/A":
                        value = None

                    if key == "ID :":
                        req_id = value
                    elif key == "Object Type :":
                        object_type = value
                        definition_next = True
                    elif key == "Source :":
                        source = value
                    elif key == "Verification Method :":
                        verification = value
                    elif key == "Compliance :":
                        compliance = value
                    elif key == "Subsystem Allocation :":
                        allocation = value
                    elif key == "Justification & Comments :":
                        comments = value
                        justification_next = True
                    elif key == "Compliance Comment :":
                        compliance_comment = value

                    line_has_keyword = True
                    break

            if definition_next and not line_has_keyword:
                definition += " " + line
            
            if justification_next and not line_has_keyword:
                comments += " " + line

        print(f"\nFound values:")
        print(f"  ID: {req_id}")
        print(f"  Object Type: {object_type}")
        print(f"  Definition: {definition}")
        print(f"  Source: {source}")
        print(f"  Verification Method: {verification}")
        print(f"  Compliance: {compliance}")
        print(f"  Subsystem Allocation: {allocation}")
        print(f"  Justification & Comments: {comments}")
        print(f"  Compliance Comment: {compliance_comment}")
        print()

        requirements.append(Requirement(
            id=req_id,
            object_type=object_type,
            definition=definition,
            source=source,
            verification=verification,
            compliance=compliance,
            allocation=allocation,
            comments=comments,
            compliance_comment=compliance_comment
        ))

    file_name = os.path.splitext(os.path.basename(file))[0]
    export_requirements_to_excel(requirements, f"output/{file_name}.csv")
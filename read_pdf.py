import pandas as pd
import pymupdf # imports the pymupdf library
import re

file = r"requirement_documents/sample_requirements_specification.pdf"

doc = pymupdf.open(file)

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
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)

complete_doc_split = []
for page in doc:
  text = page.get_text() # pyright: ignore[reportAttributeAccessIssue]
  page_split = [re.sub(r'\s+', ' ', item.strip()) for item in text[120:].split("\n") if item.strip() != '']
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

#print(*all_reqs, sep="\n\n")



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

export_requirements_to_excel(requirements, "output/extracted_requirements.csv")
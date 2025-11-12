"""
Performance comparison for keyword parsing in PDF processor.
"""

import time
from typing import Dict, List

# Sample data
KEYWORDS = {
    "ID :": "requirement_id",
    "Object Type :": "type",
    "Source :": "source",
    "Verification :": "verification",
    "Compliance :": "compliance",
    "Allocation :": "allocation",
    "Comments :": "comments",
    "Compliance Comment :": "compliance_comment",
}

# Sample block (realistic data)
sample_block = [
    "ID : REQ-001",
    "Object Type : Functional",
    "This is a multi-line definition that continues",
    "across multiple lines of text",
    "Source : System Requirements Document",
    "Verification : Test",
    "Compliance : Mandatory",
    "Allocation : Software Team",
    "Comments : This is a comment that spans",
    "multiple lines as well",
    "to simulate real data",
    "Compliance Comment : Fully compliant"
]

# Multiply to make test more realistic
test_blocks = [sample_block] * 1000


def current_approach(block: List[str]) -> Dict[str, str]:
    """Current implementation with if-elif chain."""
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
    
    current_multiline_field = None
    
    for line in block:
        line_has_keyword = False
        
        # Check each keyword
        for keyword, field in KEYWORDS.items():
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
    
    return fields


def optimized_approach(block: List[str]) -> Dict[str, str]:
    """Optimized implementation with dictionary dispatch."""
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
    
    # Dictionary mapping fields to their continuation targets
    multiline_map = {
        "type": "definition",
        "comments": "comments"
    }
    
    current_multiline_field = None
    
    for line in block:
        line_has_keyword = False
        
        # Check each keyword
        for keyword, field in KEYWORDS.items():
            if keyword in line:
                value = line.replace(keyword, '').strip()
                fields[field] = value
                
                # Use dictionary lookup for multi-line continuation
                current_multiline_field = multiline_map.get(field)
                
                line_has_keyword = True
                break
        
        # Handle multi-line continuation
        if not line_has_keyword and current_multiline_field:
            fields[current_multiline_field] += " " + line
    
    return fields


def most_optimized_approach(block: List[str]) -> Dict[str, str]:
    """Most optimized with startswith for early exit."""
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
    
    # Dictionary mapping fields to their continuation targets
    multiline_map = {
        "type": "definition",
        "comments": "comments"
    }
    
    current_multiline_field = None
    
    for line in block:
        matched = False
        
        # Use startswith for faster matching
        for keyword, field in KEYWORDS.items():
            if line.startswith(keyword):
                fields[field] = line[len(keyword):].strip()
                current_multiline_field = multiline_map.get(field)
                matched = True
                break
        
        # Handle multi-line continuation
        if not matched and current_multiline_field:
            fields[current_multiline_field] += " " + line
    
    return fields


def read_pdf_approach(block: List[str]) -> Dict[str, str]:
    """Original read_pdf.py approach with individual variables."""
    req_id = ""
    object_type = ""
    definition = ""
    source = ""
    verification = ""
    compliance = ""
    allocation = ""
    comments = ""
    compliance_comment = ""
    
    definition_next = False
    justification_next = False
    
    for line in block:
        line_has_keyword = False
        
        for key in KEYWORDS.keys():
            if line.startswith(key):
                definition_next = False
                justification_next = False
                value = line.replace(key, "").strip()
                
                if key == "ID :":
                    req_id = value
                elif key == "Object Type :":
                    object_type = value
                    definition_next = True
                elif key == "Source :":
                    source = value
                elif key == "Verification :":
                    verification = value
                elif key == "Compliance :":
                    compliance = value
                elif key == "Allocation :":
                    allocation = value
                elif key == "Comments :":
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
    
    return {
        "requirement_id": req_id,
        "type": object_type,
        "definition": definition,
        "source": source,
        "verification": verification,
        "compliance": compliance,
        "allocation": allocation,
        "comments": comments,
        "compliance_comment": compliance_comment
    }


def benchmark(func, blocks, iterations=10):
    """Run benchmark test."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        for block in blocks:
            func(block)
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    return avg_time


if __name__ == "__main__":
    print("=" * 60)
    print("PDF Processor Performance Test")
    print(f"Testing with {len(test_blocks)} requirement blocks")
    print("=" * 60)
    
    # Warm-up
    for block in test_blocks[:10]:
        current_approach(block)
        optimized_approach(block)
        most_optimized_approach(block)
        read_pdf_approach(block)
    
    # Benchmarks
    print("\nRunning benchmarks...\n")
    
    time1 = benchmark(current_approach, test_blocks)
    print(f"Current approach (if-elif):        {time1:.4f}s")
    
    time2 = benchmark(optimized_approach, test_blocks)
    print(f"Optimized approach (dict lookup):  {time2:.4f}s")
    
    time3 = benchmark(most_optimized_approach, test_blocks)
    print(f"Most optimized (startswith):       {time3:.4f}s")
    
    time4 = benchmark(read_pdf_approach, test_blocks)
    print(f"read_pdf.py approach (variables):  {time4:.4f}s")
    
    print("\n" + "=" * 60)
    print("Performance Improvement:")
    print("=" * 60)
    
    improvement1 = ((time1 - time2) / time1) * 100
    improvement2 = ((time1 - time3) / time1) * 100
    improvement3 = ((time1 - time4) / time1) * 100
    
    print(f"Dict lookup vs Current:      {improvement1:+.1f}%")
    print(f"Startswith vs Current:       {improvement2:+.1f}%")
    print(f"read_pdf.py vs Current:      {improvement3:+.1f}%")
    
    # Verify correctness
    print("\n" + "=" * 60)
    print("Correctness check:")
    print("=" * 60)
    
    result1 = current_approach(sample_block)
    result2 = optimized_approach(sample_block)
    result3 = most_optimized_approach(sample_block)
    result4 = read_pdf_approach(sample_block)
    
    print(f"Current == Optimized:        {result1 == result2}")
    print(f"Current == Most Optimized:   {result1 == result3}")
    print(f"Current == read_pdf.py:      {result1 == result4}")
    
    if result1 != result2 or result1 != result3 or result1 != result4:
        print("\nResults differ!")
        print("\nCurrent:", result1)
        print("\nOptimized:", result2)
        print("\nMost Optimized:", result3)
        print("\nread_pdf.py:", result4)
    else:
        print("\nAll approaches produce identical results!")

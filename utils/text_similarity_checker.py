#!/usr/bin/env python3
"""
Text Similarity Checker for Requirements Analysis
===============================================

Compares text similarity between requirements from different CSV files.
Uses Jaccard similarity coefficient with length balancing to identify
potentially related requirements across datasets.

Features:
- Word-based similarity calculation with Jaccard coefficient
- Length balancing to handle texts of different sizes
- Configurable similarity thresholds
- Detailed reporting with similarity levels
- Support for different CSV column structures

Usage:
    python text_similarity_checker.py req_file.csv toplevel_file.csv
    python text_similarity_checker.py --help

Author: Requirements Management Tool Team
Date: November 2025
"""

# Standard library imports
import csv
import re
import argparse
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

def clean_text(text: Optional[str]) -> str:
    """
    Clean text for better comparison by normalizing whitespace and case.
    
    Removes extra whitespace, normalizes to lowercase, and removes quotes
    to create a standardized format for text comparison.
    
    Args:
        text: Raw text string to clean (can be None or empty)
        
    Returns:
        str: Cleaned text with normalized whitespace and case
        
    Example:
        >>> clean_text('  "Hello    World"  ')
        'hello world'
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize case
    cleaned = re.sub(r'\s+', ' ', text.strip().lower()).replace('"', '')
    return cleaned


def remove_quotes(text: Optional[str]) -> str:
    """
    Remove surrounding quotes from text.
    
    Handles both single and double quotes that surround the entire text.
    Only removes quotes that appear at both the beginning and end.
    
    Args:
        text: Text string that may have surrounding quotes
        
    Returns:
        str: Text with surrounding quotes removed
        
    Example:
        >>> remove_quotes('"Hello World"')
        'Hello World'
        >>> remove_quotes("'Test text'")
        'Test text'
    """
    if not text:
        return text or ""
    
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1]
    return text

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate word-based similarity between two texts using Jaccard coefficient.
    
    Uses Jaccard similarity with length balancing to handle texts of different
    sizes fairly. The algorithm:
    1. Calculates Jaccard coefficient (common words / total unique words)
    2. Applies length balance factor to penalize very different text lengths
    3. Returns weighted similarity score
    
    Args:
        text1: First text to compare
        text2: Second text to compare
        
    Returns:
        float: Similarity score between 0.0 (no similarity) and 1.0 (identical)
        
    Example:
        >>> calculate_similarity("hello world", "hello universe")
        0.33  # One common word out of three unique words
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0.0
        
    common_words = words1 & words2
    total_unique_words = len(words1 | words2)
    
    # Jaccard similarity coefficient
    jaccard_similarity = len(common_words) / total_unique_words if total_unique_words > 0 else 0
    
    # Length balance factor to penalize very different text lengths
    len1, len2 = len(words1), len(words2)
    length_ratio = min(len1, len2) / max(len1, len2) if max(len1, len2) > 0 else 0
    
    # Weighted similarity considering both overlap and length similarity
    balanced_similarity = jaccard_similarity * (0.7 + 0.3 * length_ratio)
    
    return balanced_similarity

def refined_similarity(text1: str, text2: str) -> float:

    text_list1 = text1.split()
    text_list2 = text2.split()

    initial_lengths = (len(text_list1), len(text_list2))

    matches = 0
    consistency_indices = []
    for word in text_list1:
        if word in text_list2:
            index = text_list2.index(word) 
            text_list2.remove(word)
            matches += 1
            consistency_indices.append(1/index if index>0 else 1)

    # if len(consistency_indices)>10:
    #     print(consistency_indices)
    #     input()

    text1_ratio = matches / initial_lengths[0] if initial_lengths[0] > 0 else 0
    text2_ratio = len(text_list2) / initial_lengths[1] if initial_lengths[1] > 0 else 0

    alpha = 1 * np.e
    beta = 2
    similarity = np.exp(-alpha * (1 - text1_ratio)**beta - alpha * (text2_ratio)**beta)
    
    #similarity = 1-(((text1_ratio-1)**2+(text2_ratio)**2)/2)

    return matches, text1_ratio, text2_ratio, similarity, consistency_indices, len(consistency_indices)


def get_similarity_level(similarity: float) -> str:
    """
    Return a descriptive text level based on similarity score.
    
    Categorizes similarity scores into human-readable levels for
    easier interpretation of results.
    
    Args:
        similarity: Similarity score between 0.0 and 1.0
        
    Returns:
        str: Similarity level description
        
    Thresholds:
        >= 0.7: "HIGH"
        >= 0.4: "MEDIUM" 
        >= 0.2: "LOW-MEDIUM"
        < 0.2:  "LOW"
    """
    if similarity >= 0.7:
        return "HIGH"
    elif similarity >= 0.4:
        return "MEDIUM"
    elif similarity >= 0.2:
        return "LOW-MEDIUM"
    else:
        return "LOW"


def load_requirements_data(file_path: Path, id_column: str = 'TopLevelReq',  
                          text_column: str = 'Text') -> List[Dict[str, str]]:
    """
    Load requirements data from CSV file.
    
    Extracts requirement IDs and associated text content for similarity analysis.
    
    Args:
        file_path: Path to CSV file containing requirements
        id_column: Name of column containing requirement IDs
        text_column: Name of column containing full text descriptions
        
    Returns:
        List of dictionaries with 'id', 'text', 'original', and 'type' keys
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        KeyError: If required columns are missing
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {file_path}")
    
    req_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            
            # Verify required columns exist
            if id_column not in reader.fieldnames:
                raise KeyError(f"Required column '{id_column}' not found in {file_path}")
            
            for row in reader:
                req_id = row[id_column].strip()
                
                # Process full text if available  
                if text_column in row and row[text_column].strip():
                    text = row[text_column].strip()
                    req_data.append({
                        'id': req_id,
                        'text': clean_text(text),
                        'original': text,
                        'type': 'Text'
                    })
                    
    except Exception as e:
        raise RuntimeError(f"Error reading requirements file {file_path}: {e}")
    
    return req_data


def load_toplevel_data(file_path: Path, id_column: str = 'Requirement ID',
                      definition_column: str = 'Definition') -> List[Dict[str, str]]:
    """
    Load top-level requirements data from CSV file.
    
    Extracts requirement IDs and definitions for comparison with other datasets.
    
    Args:
        file_path: Path to CSV file containing top-level requirements
        id_column: Name of column containing requirement IDs
        definition_column: Name of column containing requirement definitions
        
    Returns:
        List of dictionaries with 'id', 'text', 'original', and 'type' keys
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        KeyError: If required columns are missing
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Top-level file not found: {file_path}")
    
    toplevel_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            
            # Verify required columns exist
            required_cols = [id_column, definition_column]
            missing_cols = [col for col in required_cols if col not in reader.fieldnames]
            if missing_cols:
                raise KeyError(f"Required columns {missing_cols} not found in {file_path}")
            
            for row in reader:
                req_id = row[id_column].strip()
                definition = row[definition_column].strip()
                
                if definition:
                    cleaned_definition = remove_quotes(definition)
                    toplevel_data.append({
                        'id': req_id,
                        'text': clean_text(cleaned_definition),
                        'original': cleaned_definition,
                        'type': 'Definition'
                    })
                    
    except Exception as e:
        raise RuntimeError(f"Error reading top-level file {file_path}: {e}")
    
    return toplevel_data


def analyze_text_similarity(req_data: List[Dict[str, str]], 
                          toplevel_data: List[Dict[str, str]],
                          high_threshold: float = 0.7,
                          medium_threshold: float = 0.4) -> List[Dict[str, any]]:
    """
    Analyze text similarity between requirements and top-level data.
    
    Compares all text pairs and identifies similarities above the specified
    thresholds. Returns detailed results for further analysis.
    
    Args:
        req_data: List of requirement text items
        toplevel_data: List of top-level requirement items
        high_threshold: Minimum similarity for "high" classification (default: 0.7)
        medium_threshold: Minimum similarity for reporting (default: 0.4)
        
    Returns:
        List of similarity match dictionaries, sorted by similarity (highest first)
        
    Example:
        >>> matches = analyze_text_similarity(req_data, toplevel_data)
        >>> print(f"Found {len(matches)} similar text pairs")
    """
    print(f"Analyzing text similarity...")
    print(f"Comparing {len(req_data)} texts with {len(toplevel_data)} definitions")
    
    similarities = []
    total_comparisons = len(req_data) * len(toplevel_data)
    processed = 0

    with open("similarity_debug_output.csv", "w", encoding="utf-8") as debug_file:
        debug_file.write("id;toplevel_id;similarity;matches;text1_ratio;text2_ratio;similarity2;consistency_indices;consistency_count;text1;text2;ai_similarity\n")
    
        for req_item in req_data:
            for toplevel_item in toplevel_data:
                processed += 1
                
                # Show progress for large datasets
                if processed % 1000 == 0 or processed == total_comparisons:
                    progress = (processed / total_comparisons) * 100
                    print(f"Progress: {progress:.1f}% ({processed:,}/{total_comparisons:,} comparisons)")
                
                similarity = calculate_similarity(req_item['text'], toplevel_item['text'])
                refined_similarity_result = refined_similarity(req_item['text'], toplevel_item['text'])
                # if refined_similarity_result[-1] >= 10:
                #     ai_similarity = compute_text_similarity(req_item['text'], toplevel_item['text'])
                # else:
                #     continue
                #print(f"{similarity:.3f};{refined_similarity(req_item['text'], toplevel_item['text'])}")

                ai_similarity = 0
                debug_file.write(f"{req_item['id']};{toplevel_item['id']};{similarity:.3f};{';'.join(map(str, refined_similarity_result))};{req_item['text'].replace(';', ',')};{toplevel_item['text'].replace(';', ',')};{ai_similarity:.3f}\n")
                
                if similarity >= medium_threshold:
                    similarities.append({
                        'req_id': req_item['id'],
                        'req_type': req_item['type'],
                        'req_text': req_item['original'],
                        'toplevel_id': toplevel_item['id'],
                        'toplevel_text': toplevel_item['original'],
                        'similarity': similarity
                    })
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    return similarities


def print_similarity_results(similarities: List[Dict[str, any]], 
                           high_threshold: float = 0.7,
                           medium_threshold: float = 0.4) -> None:
    """
    Print formatted similarity analysis results.
    
    Args:
        similarities: List of similarity matches from analyze_text_similarity
        high_threshold: Threshold for "high" similarity classification
        medium_threshold: Threshold for "medium" similarity classification
    """
    if not similarities:
        print("\nNo significant text similarities found.")
        print("Suggestions:")
        print("  - Try lowering the similarity threshold")
        print("  - Verify the files contain expected text columns")
        print("  - Check that column names match the expected format")
        return
    
    print("\nSIMILAR TEXTS FOUND (sorted by similarity):")
    print("=" * 80)
    
    # Show high similarity matches in detail
    high_matches = [s for s in similarities if s['similarity'] >= high_threshold]
    
    for match in high_matches:
        level = get_similarity_level(match['similarity'])
        print(f"Similarity: {match['similarity']:.3f} ({level})")
        print(f"   REQ: {match['req_id']} ({match['req_type']})")
        req_preview = match['req_text'][:100] + ('...' if len(match['req_text']) > 100 else '')
        print(f"        \"{req_preview}\"")
        print(f"   TOP: {match['toplevel_id']} (Definition)")
        top_preview = match['toplevel_text'][:100] + ('...' if len(match['toplevel_text']) > 100 else '')
        print(f"        \"{top_preview}\"")
        print()
    
    # Summary statistics
    high_sim_count = len([s for s in similarities if s['similarity'] >= high_threshold])
    medium_sim_count = len([s for s in similarities if medium_threshold <= s['similarity'] < high_threshold])
    
    print("\nSUMMARY:")
    print(f"   High similarity (>={high_threshold*100:.0f}%): {high_sim_count} matches")
    print(f"   Medium similarity ({medium_threshold*100:.0f}-{high_threshold*100-1:.0f}%): {medium_sim_count} matches")
    print(f"   Total matches found: {len(similarities)}")
    
    # Best match
    if similarities:
        best_match = similarities[0]
        print(f"   Best match: {best_match['similarity']:.1%} similarity")
        print(f"       {best_match['req_id']} ↔ {best_match['toplevel_id']}")


def main() -> int:
    """
    Main function for text similarity analysis CLI.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog='text_similarity_checker.py',
        description='Compare text similarity between requirements from different CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare requirements files with default column names
  %(prog)s requirements.csv toplevel.csv
  
  # Use custom similarity thresholds
  %(prog)s requirements.csv toplevel.csv --high-threshold 0.8 --medium-threshold 0.3
  
  # Specify custom column names
  %(prog)s requirements.csv toplevel.csv --req-id-col "ID" --def-col "Description"

Column expectations:
  Requirements file: Requirement ID, Definition (configurable)
  Top-level file: Requirement ID, Definition (configurable)
        """
    )
    
    # Required arguments
    parser.add_argument(
        'req_file',
        type=Path,
        help='CSV file containing requirements data'
    )
    
    parser.add_argument(
        'toplevel_file', 
        type=Path,
        help='CSV file containing top-level requirements data'
    )
    
    # Column name configuration
    parser.add_argument(
        '--req-id-col',
        default='TopLevelReq',
        help='Column name for requirement IDs in requirements file (default: TopLevelReq)'
    )
    
    parser.add_argument(
        '--text-col',
        default='Text',
        help='Column name for full text in requirements file (default: Text)'
    )
    
    parser.add_argument(
        '--toplevel-id-col',
        default='Requirement ID',
        help='Column name for requirement IDs in top-level file (default: "Requirement ID")'
    )
    
    parser.add_argument(
        '--def-col',
        default='Definition',
        help='Column name for definitions in top-level file (default: Definition)'
    )
    
    # Similarity thresholds
    parser.add_argument(
        '--high-threshold',
        type=float,
        default=0.7,
        help='Minimum similarity for high classification (default: 0.7)'
    )
    
    parser.add_argument(
        '--medium-threshold',
        type=float,
        default=0.4,
        help='Minimum similarity for reporting (default: 0.4)'
    )
    
    # Verbose output
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    for file_path in [args.req_file, args.toplevel_file]:
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return 1
        if not file_path.is_file():
            print(f"Error: Path is not a file: {file_path}")
            return 1
    
    # Validate thresholds
    if not (0.0 <= args.high_threshold <= 1.0):
        print(f"Error: High threshold must be between 0.0 and 1.0, got {args.high_threshold}")
        return 1
    
    if not (0.0 <= args.medium_threshold <= 1.0):
        print(f"Error: Medium threshold must be between 0.0 and 1.0, got {args.medium_threshold}")
        return 1
    
    if args.medium_threshold > args.high_threshold:
        print(f"Error: Medium threshold ({args.medium_threshold}) cannot be higher than high threshold ({args.high_threshold})")
        return 1
    
    try:
        print("=== TEXT SIMILARITY ANALYSIS ===")
        print(f"Requirements file: {args.req_file}")
        print(f"Top-level file: {args.toplevel_file}")
        print(f"High similarity threshold: {args.high_threshold:.1%}")
        print(f"Medium similarity threshold: {args.medium_threshold:.1%}")
        print()
        
        # Load data
        print("Loading requirements data...")
        req_data = load_requirements_data(
            args.req_file,
            args.req_id_col,
            args.text_col
        )
        print(f"Loaded {len(req_data)} requirement text entries")
        
        print("Loading top-level data...")
        toplevel_data = load_toplevel_data(
            args.toplevel_file,
            args.toplevel_id_col,
            args.def_col
        )
        print(f"Loaded {len(toplevel_data)} top-level definitions")
        
        if not req_data:
            print("Warning: No requirement texts found")
            return 0
        
        if not toplevel_data:
            print("Warning: No top-level definitions found")
            return 0
        
        # Perform analysis
        similarities = analyze_text_similarity(
            req_data,
            toplevel_data, 
            args.high_threshold,
            args.medium_threshold
        )
        
        # Print results
        print_similarity_results(similarities, args.high_threshold, args.medium_threshold)
        
        print(f"\nFiles analyzed:")
        print(f"   Requirements: {args.req_file} ({len(req_data)} text entries)")
        print(f"   Top-level: {args.toplevel_file} ({len(toplevel_data)} definitions)")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled by user.")
        return 130
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user (Ctrl+C).")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
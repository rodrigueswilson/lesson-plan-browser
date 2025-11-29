#!/usr/bin/env python3
"""
Debug the Thursday issue in ObjectivesPrinter.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_printer import extract_subject_from_unit_lesson


def debug_thursday():
    """Debug why Thursday is not detecting Math."""
    print("DEBUGGING THURSDAY ISSUE")
    print("-" * 40)
    
    unit_lesson = "Unit 5: DAILY ACTIVITIES"
    detected = extract_subject_from_unit_lesson(unit_lesson)
    
    print(f"Unit lesson: '{unit_lesson}'")
    print(f"Detected subject: '{detected}'")
    print()
    
    # Check the math patterns
    import re
    
    unit_upper = unit_lesson.upper()
    print(f"Uppercase: '{unit_upper}'")
    
    # Check explicit patterns
    print("\nChecking explicit patterns:")
    explicit_patterns = {
        r'\bMATH\b': 'Math',
        r'\bELA\b': 'ELA',
        r'\bSCIENCE\b': 'Science',
    }
    
    for pattern, subject in explicit_patterns.items():
        match = re.search(pattern, unit_upper)
        print(f"  {pattern}: {match}")
    
    # Check math keywords
    print("\nChecking math keywords:")
    math_keywords = ['UNIT', 'MULTIPLICATION', 'AREA', 'MEASURE']
    
    for keyword in math_keywords:
        match = re.search(r'\b' + keyword + r'\b', unit_upper)
        print(f"  {keyword}: {match}")
    
    print()
    
    # Test the actual function step by step
    print("Step-by-step detection:")
    
    # Pattern 1: Explicit subject prefixes
    subject_patterns = {
        r'\bMATH\b': 'Math',
        r'\bELA\b': 'ELA',
        r'\bENGLISH\b': 'ELA',
        r'\bREADING\b': 'ELA',
        r'\bWRITING\b': 'ELA',
        r'\bSCIENCE\b': 'Science',
        r'\bSOCIAL STUDIES\b': 'Social Studies',
        r'\bHISTORY\b': 'Social Studies',
        r'\bGEOGRAPHY\b': 'Social Studies',
        r'\bART\b': 'Art',
        r'\bMUSIC\b': 'Music',
        r'\bPE\b': 'Physical Education',
        r'\bPHYSICAL EDUCATION\b': 'Physical Education',
        r'\bHEALTH\b': 'Health',
        r'\bLIBRARY\b': 'Library',
        r'\bTECH\b': 'Technology',
        r'\bTECHNOLOGY\b': 'Technology',
        r'\bCOMPUTER\b': 'Technology',
    }
    
    for pattern, subject in subject_patterns.items():
        if re.search(pattern, unit_upper):
            print(f"  Matched explicit pattern: {pattern} -> {subject}")
            return
    
    # Pattern 2: Math-specific keywords
    math_keywords = [
        'MULTIPLICATION', 'DIVISION', 'ADDITION', 'SUBTRACTION',
        'MEASURE', 'AREA', 'PERIMETER', 'GEOMETRY', 'FRACTIONS',
        'DECIMALS', 'PLACE VALUE', 'NUMBER', 'CALCULATION',
        'EQUATION', 'PROBLEM SOLVING', 'MATH CHAPTER', 'UNIT .* LESSON'
    ]
    
    for keyword in math_keywords:
        if re.search(r'\b' + keyword + r'\b', unit_upper):
            print(f"  Matched math keyword: {keyword} -> Math")
            return
    
    print("  No patterns matched, returning 'Unknown'")


if __name__ == "__main__":
    debug_thursday()

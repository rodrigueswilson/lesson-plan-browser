"""
Subject detection from unit/lesson text for objectives PDF generation.
"""

import re


def extract_subject_from_unit_lesson(unit_lesson: str) -> str:
    """
    Extract the actual subject from the unit_lesson text.

    This function parses patterns like:
    - "Unit 3 Lesson 9: MEASURE TO FIND THE AREA" -> "Math"
    - "Math Chapter 5: MULTIPLICATION FACTS" -> "Math"
    - "ELA Unit 2: READING COMPREHENSION" -> "ELA"
    - "Science Lab: PLANT GROWTH" -> "Science"

    Args:
        unit_lesson: The unit/lesson text from the lesson plan

    Returns:
        Detected subject name or "Unknown" if not found
    """
    if not unit_lesson or not isinstance(unit_lesson, str):
        return "Unknown"

    unit_lesson = unit_lesson.strip().upper()

    # Pattern 1: Explicit subject prefixes
    subject_patterns = {
        r"\bMATH\b": "Math",
        r"\bELA\b": "ELA",
        r"\bENGLISH\b": "ELA",
        r"\bREADING\b": "ELA",
        r"\bWRITING\b": "ELA",
        r"\bSCIENCE\b": "Science",
        r"\bSOCIAL STUDIES\b": "Social Studies",
        r"\bHISTORY\b": "Social Studies",
        r"\bGEOGRAPHY\b": "Social Studies",
        r"\bART\b": "Art",
        r"\bMUSIC\b": "Music",
        r"\bPE\b": "Physical Education",
        r"\bPHYSICAL EDUCATION\b": "Physical Education",
        r"\bHEALTH\b": "Health",
        r"\bLIBRARY\b": "Library",
        r"\bTECH\b": "Technology",
        r"\bTECHNOLOGY\b": "Technology",
        r"\bCOMPUTER\b": "Technology",
    }

    for pattern, subject in subject_patterns.items():
        if re.search(pattern, unit_lesson):
            return subject

    # Pattern 2: Math-specific keywords
    math_keywords = [
        "MULTIPLICATION",
        "DIVISION",
        "ADDITION",
        "SUBTRACTION",
        "MEASURE",
        "AREA",
        "PERIMETER",
        "GEOMETRY",
        "FRACTIONS",
        "DECIMALS",
        "PLACE VALUE",
        "NUMBER",
        "CALCULATION",
        "EQUATION",
        "PROBLEM SOLVING",
        "MATH CHAPTER",
        "UNIT .* LESSON",
        "UNIT",
    ]

    for keyword in math_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Math"

    # Pattern 3: ELA-specific keywords
    ela_keywords = [
        "READING",
        "COMPREHENSION",
        "GRAMMAR",
        "SPELLING",
        "VOCABULARY",
        "WRITING",
        "PHONICS",
        "LITERATURE",
        "STORY",
        "POEM",
        "ESSAY",
        "LANGUAGE ARTS",
    ]

    for keyword in ela_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "ELA"

    # Pattern 4: Science-specific keywords
    science_keywords = [
        "EXPERIMENT",
        "LAB",
        "ORGANISM",
        "HABITAT",
        "ECOSYSTEM",
        "MATTER",
        "ENERGY",
        "FORCE",
        "MOTION",
        "PLANT",
        "ANIMAL",
    ]

    for keyword in science_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Science"

    # Pattern 5: Social Studies keywords
    ss_keywords = [
        "COMMUNITY",
        "GOVERNMENT",
        "HISTORY",
        "GEOGRAPHY",
        "CULTURE",
        "SOCIETY",
        "CIVICS",
        "ECONOMICS",
    ]

    for keyword in ss_keywords:
        if re.search(r"\b" + keyword + r"\b", unit_lesson):
            return "Social Studies"

    return "Unknown"

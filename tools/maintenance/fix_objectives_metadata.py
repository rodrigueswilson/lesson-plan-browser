#!/usr/bin/env python3
"""
Fix for objectives PDF generator metadata mismatch.

This script provides a corrected version of ObjectivesPDFGenerator.extract_objectives()
that properly determines the subject from each day's unit_lesson field.
"""

import json
import re
from typing import Dict, List, Any, Optional


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
        if re.search(pattern, unit_lesson):
            return subject
    
    # Pattern 2: Math-specific keywords
    math_keywords = [
        'MULTIPLICATION', 'DIVISION', 'ADDITION', 'SUBTRACTION',
        'MEASURE', 'AREA', 'PERIMETER', 'GEOMETRY', 'FRACTIONS',
        'DECIMALS', 'PLACE VALUE', 'NUMBER', 'CALCULATION',
        'EQUATION', 'PROBLEM SOLVING', 'MATH CHAPTER', 'UNIT .* LESSON'
    ]
    
    for keyword in math_keywords:
        if re.search(r'\b' + keyword + r'\b', unit_lesson):
            return 'Math'
    
    # Pattern 3: ELA-specific keywords
    ela_keywords = [
        'READING', 'COMPREHENSION', 'GRAMMAR', 'SPELLING',
        'VOCABULARY', 'WRITING', 'PHONICS', 'LITERATURE',
        'STORY', 'POEM', 'ESSAY', 'LANGUAGE ARTS'
    ]
    
    for keyword in ela_keywords:
        if re.search(r'\b' + keyword + r'\b', unit_lesson):
            return 'ELA'
    
    # Pattern 4: Science-specific keywords
    science_keywords = [
        'EXPERIMENT', 'LAB', 'ORGANISM', 'HABITAT', 'ECOSYSTEM',
        'MATTER', 'ENERGY', 'FORCE', 'MOTION', 'PLANT', 'ANIMAL'
    ]
    
    for keyword in science_keywords:
        if re.search(r'\b' + keyword + r'\b', unit_lesson):
            return 'Science'
    
    # Pattern 5: Social Studies keywords
    ss_keywords = [
        'COMMUNITY', 'GOVERNMENT', 'HISTORY', 'GEOGRAPHY',
        'CULTURE', 'SOCIETY', 'CIVICS', 'ECONOMICS'
    ]
    
    for keyword in ss_keywords:
        if re.search(r'\b' + keyword + r'\b', unit_lesson):
            return 'Social Studies'
    
    # Default: Return "Unknown"
    return "Unknown"


class FixedObjectivesPDFGenerator:
    """Fixed version of ObjectivesPDFGenerator with correct metadata extraction."""
    
    def extract_objectives(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract objectives from lesson plan with correct subject detection."""
        objectives = []
        
        if 'days' not in lesson_json:
            return objectives
        
        metadata = lesson_json.get('metadata', {})
        week_of = metadata.get('week_of', 'Unknown')
        grade = metadata.get('grade', 'Unknown')
        homeroom = metadata.get('homeroom', 'Unknown')
        teacher_name = metadata.get('teacher_name', 'Unknown')
        
        days = lesson_json['days']
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        for day_name in day_names:
            if day_name not in days:
                continue
            
            day_data = days[day_name]
            
            # Skip if no objective
            objective_data = day_data.get('objective', {})
            if not objective_data:
                continue
            
            # Skip "No School" entries
            unit_lesson = day_data.get('unit_lesson', '')
            if unit_lesson and unit_lesson.strip().lower() == 'no school':
                continue
            
            # Check if all objective fields are "No School"
            content_obj = objective_data.get('content_objective', '').strip().lower()
            student_goal = objective_data.get('student_goal', '').strip().lower()
            wida_obj = objective_data.get('wida_objective', '').strip().lower()
            
            if (content_obj == 'no school' and 
                student_goal == 'no school' and 
                wida_obj == 'no school'):
                continue
            
            # *** THE FIX: Extract subject from unit_lesson instead of using metadata ***
            detected_subject = extract_subject_from_unit_lesson(unit_lesson)
            
            # If we can't detect from unit_lesson, fall back to metadata
            if detected_subject == "Unknown":
                detected_subject = metadata.get('subject', 'Unknown')
            
            objectives.append({
                'week_of': week_of,
                'day': day_name.capitalize(),
                'subject': detected_subject,  # Use detected subject
                'grade': grade,
                'homeroom': homeroom,
                'teacher_name': teacher_name,
                'unit_lesson': unit_lesson,
                'content_objective': objective_data.get('content_objective', ''),
                'student_goal': objective_data.get('student_goal', ''),
                'wida_objective': objective_data.get('wida_objective', '')
            })
        
        return objectives


def test_fix():
    """Test the fixed extraction method."""
    print("=" * 80)
    print("TESTING FIXED OBJECTIVES PDF GENERATOR")
    print("=" * 80)
    print()
    
    # Create test lesson with mixed subjects
    test_lesson = {
        "metadata": {
            "week_of": "11-17-11-21",
            "grade": "3",
            "subject": "ELA",  # This is wrong for some days
            "homeroom": "Room 15",
            "teacher_name": "Ms. Wilson"
        },
        "days": {
            "monday": {
                "unit_lesson": "Unit 3 Lesson 9: MEASURE TO FIND THE AREA",
                "objective": {
                    "content_objective": "Students will measure area using square units.",
                    "student_goal": "I will find the area of shapes using square units.",
                    "wida_objective": "Students will use language to describe areas."
                }
            },
            "tuesday": {
                "unit_lesson": "ELA Unit 2: READING COMPREHENSION",
                "objective": {
                    "content_objective": "Students will improve reading comprehension.",
                    "student_goal": "I will understand what I read better.",
                    "wida_objective": "Students will use reading strategies."
                }
            },
            "wednesday": {
                "unit_lesson": "Science Lab: PLANT GROWTH EXPERIMENT",
                "objective": {
                    "content_objective": "Students will conduct plant growth experiments.",
                    "student_goal": "I will watch how plants grow.",
                    "wida_objective": "Students will use scientific observation language."
                }
            }
        }
    }
    
    # Test the fixed generator
    fixed_gen = FixedObjectivesPDFGenerator()
    objectives = fixed_gen.extract_objectives(test_lesson)
    
    print("Fixed extraction results:")
    print("-" * 40)
    for i, obj in enumerate(objectives, 1):
        print(f"{i}. {obj['day']}:")
        print(f"   Subject: {obj['subject']}")
        print(f"   Unit: {obj['unit_lesson']}")
        print(f"   Student Goal: {obj['student_goal']}")
        print()
    
    print("Validation:")
    print("-" * 40)
    
    # Check if subjects match the unit content
    validations = []
    for obj in objectives:
        unit = obj['unit_lesson'].upper()
        subject = obj['subject']
        
        if 'MEASURE' in unit or 'AREA' in unit:
            validations.append(("Math content detected", subject == "Math", subject))
        elif 'ELA' in unit or 'READING' in unit:
            validations.append(("ELA content detected", subject == "ELA", subject))
        elif 'SCIENCE' in unit or 'PLANT' in unit:
            validations.append(("Science content detected", subject == "Science", subject))
    
    all_correct = True
    for description, is_correct, detected in validations:
        status = "✓" if is_correct else "✗"
        print(f"{status} {description}: {detected}")
        if not is_correct:
            all_correct = False
    
    print()
    if all_correct:
        print("✓ ALL SUBJECTS CORRECTLY DETECTED!")
    else:
        print("✗ Some subjects are incorrectly detected.")
    
    print()
    print("=" * 80)
    print("FIX VERIFICATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_fix()

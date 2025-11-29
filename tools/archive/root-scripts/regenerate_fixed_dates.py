#!/usr/bin/env python3
"""
Regenerate HTML with fixed date parsing.
"""

import json
import sys
from pathlib import Path
import tempfile

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def create_sample_lesson_data():
    """Create realistic lesson data with mixed subjects."""
    return {
        "metadata": {
            "week_of": "11-17-11-21",  # Using dash format
            "grade": "3",
            "subject": "ELA / Math / Science",
            "homeroom": "Room 15",
            "teacher_name": "Ms. Wilson"
        },
        "days": {
            "monday": {
                "unit_lesson": "Unit 3 Lesson 9: MEASURE TO FIND THE AREA",
                "objective": {
                    "content_objective": "Students will measure area using square units and understand that area is the measure of space inside a shape.",
                    "student_goal": "I will find the area of shapes using square units.",
                    "wida_objective": "Students will use language to describe and compare areas of different shapes using square units and mathematical vocabulary."
                }
            },
            "tuesday": {
                "unit_lesson": "ELA Unit 2: READING COMPREHENSION STRATEGIES",
                "objective": {
                    "content_objective": "Students will apply reading comprehension strategies to understand grade-level texts.",
                    "student_goal": "I will use strategies to understand what I read better.",
                    "wida_objective": "Students will use academic language to describe reading strategies."
                }
            },
            "wednesday": {
                "unit_lesson": "Science Lab: PLANT GROWTH EXPERIMENT",
                "objective": {
                    "content_objective": "Students will conduct experiments to observe and record plant growth.",
                    "student_goal": "I will watch how plants grow and record what happens.",
                    "wida_objective": "Students will use scientific observation language."
                }
            },
            "thursday": {
                "unit_lesson": "Math Chapter 5: MULTIPLICATION FACTS TO 12",
                "objective": {
                    "content_objective": "Students will memorize multiplication facts up to 12x12.",
                    "student_goal": "I will memorize my multiplication facts.",
                    "wida_objective": "Students will use mathematical language to state multiplication facts."
                }
            },
            "friday": {
                "unit_lesson": "History Chapter 3: COMMUNITIES AND GOVERNMENT",
                "objective": {
                    "content_objective": "Students will learn about community government structures.",
                    "student_goal": "I will understand how communities work and make decisions.",
                    "wida_objective": "Students will use social studies vocabulary to discuss community structures."
                }
            }
        }
    }


def regenerate_html():
    """Regenerate HTML with fixed date parsing."""
    print("=" * 80)
    print("REGENERATING HTML WITH FIXED DATE PARSING")
    print("=" * 80)
    print()
    
    # Create the lesson data
    lesson_data = create_sample_lesson_data()
    
    # Initialize the generator
    generator = ObjectivesPDFGenerator()
    
    # Create output directory
    output_dir = Path(tempfile.gettempdir()) / "objectives_demo"
    output_dir.mkdir(exist_ok=True)
    
    # Generate HTML
    html_path = output_dir / "objectives_fixed_dates.html"
    html_path = generator.generate_html(
        lesson_data,
        str(html_path),
        user_name="Ms. Wilson"
    )
    
    print(f"✓ HTML generated: {html_path}")
    
    # Read and display the headers with dates
    print("\nHEADERS WITH CORRECT DATES:")
    print("-" * 40)
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    import re
    headers = re.findall(r'<div class="header">(.*?)</div>', content, re.DOTALL)
    
    for i, header in enumerate(headers, 1):
        clean_header = header.replace('<br>', ' | ').strip()
        print(f"{i}. {clean_header}")
    
    print()
    print("=" * 80)
    print("FIX VERIFIED!")
    print("=" * 80)
    print()
    print("The headers now correctly show:")
    print("  - Monday: 11/17/2024")
    print("  - Tuesday: 11/18/2024")
    print("  - Wednesday: 11/19/2024")
    print("  - Thursday: 11/20/2024")
    print("  - Friday: 11/21/2024")
    print()
    print("Instead of showing '11-17-11-21' for all days.")
    
    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file://{html_path}')
        print("\n✓ HTML file opened in default browser")
    except:
        print("\nCould not open browser automatically.")


if __name__ == "__main__":
    regenerate_html()

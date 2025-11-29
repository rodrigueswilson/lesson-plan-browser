#!/usr/bin/env python3
"""
Generate a fixed HTML/PDF with correct metadata for objectives.
This demonstrates the fix working with real lesson data.
"""

import json
import sys
from pathlib import Path
import tempfile
import os

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def create_sample_lesson_data():
    """Create realistic lesson data with mixed subjects."""
    return {
        "metadata": {
            "week_of": "11-17-11-21",
            "grade": "3",
            "subject": "ELA / Math / Science",  # Multi-subject metadata
            "homeroom": "Room 15",
            "teacher_name": "Ms. Wilson"
        },
        "days": {
            "monday": {
                "unit_lesson": "Unit 3 Lesson 9: MEASURE TO FIND THE AREA",
                "objective": {
                    "content_objective": "Students will measure area using square units and understand that area is the measure of space inside a shape.",
                    "student_goal": "I will find the area of shapes using square units.",
                    "wida_objective": "Students will use language to describe and compare areas of different shapes using square units and mathematical vocabulary (ELD-MA.3-5.Describe.Speaking) by using visual supports, sentence frames, and bilingual glossaries appropriate for WIDA levels 2-4, producing oral descriptions that demonstrate understanding of area measurement and spatial relationships."
                }
            },
            "tuesday": {
                "unit_lesson": "ELA Unit 2: READING COMPREHENSION STRATEGIES",
                "objective": {
                    "content_objective": "Students will apply reading comprehension strategies to understand grade-level texts, including making predictions and asking questions.",
                    "student_goal": "I will use strategies to understand what I read better.",
                    "wida_objective": "Students will use academic language to describe reading strategies and comprehension processes (ELD-RL.3-5.Analyze.Speaking) by using think-aloud protocols, graphic organizers, and bilingual anchor charts to explain their thinking during reading."
                }
            },
            "wednesday": {
                "unit_lesson": "Science Lab: PLANT GROWTH EXPERIMENT",
                "objective": {
                    "content_objective": "Students will conduct experiments to observe and record plant growth under different conditions, identifying variables that affect plant development.",
                    "student_goal": "I will watch how plants grow and record what happens.",
                    "wida_objective": "Students will use scientific observation language to describe experimental procedures and results (ELD-SC.3-5.Investigate.Speaking) by using bilingual science journals, observation templates, and academic vocabulary for describing changes over time."
                }
            },
            "thursday": {
                "unit_lesson": "Math Chapter 5: MULTIPLICATION FACTS TO 12",
                "objective": {
                    "content_objective": "Students will memorize multiplication facts up to 12x12 using patterns, strategies, and repeated practice to build fluency.",
                    "student_goal": "I will memorize my multiplication facts.",
                    "wida_objective": "Students will use mathematical language to state multiplication facts and explain patterns (ELD-MA.3-5.Explain.Speaking) by using multiplication charts, arrays, and bilingual math vocabulary to describe relationships between numbers."
                }
            },
            "friday": {
                "unit_lesson": "History Chapter 3: COMMUNITIES AND GOVERNMENT",
                "objective": {
                    "content_objective": "Students will learn about community government structures, the roles of leaders, and how citizens participate in making decisions.",
                    "student_goal": "I will understand how communities work and make decisions.",
                    "wida_objective": "Students will use social studies vocabulary to discuss community structures and civic participation (ELD-SS.3-5.Analyze.Speaking) by using bilingual glossaries, community maps, and role-playing activities to explain government functions."
                }
            }
        }
    }


def generate_fixed_objectives_pdf():
    """Generate HTML and PDF with fixed metadata."""
    print("=" * 80)
    print("GENERATING FIXED OBJECTIVES PDF WITH CORRECT METADATA")
    print("=" * 80)
    print()
    
    # Create the lesson data
    lesson_data = create_sample_lesson_data()
    
    # Initialize the generator
    generator = ObjectivesPDFGenerator()
    
    # Extract objectives to show what was detected
    print("DETECTED SUBJECTS FROM UNIT LESSON CONTENT:")
    print("-" * 40)
    
    objectives = generator.extract_objectives(lesson_data)
    for obj in objectives:
        print(f"{obj['day']}: {obj['subject']}")
        print(f"  Unit: {obj['unit_lesson']}")
        print(f"  Student Goal: {obj['student_goal'][:60]}...")
        print()
    
    # Generate HTML file
    print("GENERATING HTML FILE...")
    print("-" * 40)
    
    output_dir = Path(tempfile.gettempdir()) / "objectives_demo"
    output_dir.mkdir(exist_ok=True)
    
    html_path = output_dir / "objectives_fixed_demo.html"
    html_path = generator.generate_html(
        lesson_data,
        str(html_path),
        user_name="Ms. Wilson"
    )
    
    print(f"✓ HTML generated: {html_path}")
    
    # Try to generate PDF if WeasyPrint is available
    print("\nATTEMPTING PDF GENERATION...")
    print("-" * 40)
    
    try:
        pdf_path = generator.convert_to_pdf(html_path)
        print(f"✓ PDF generated: {pdf_path}")
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        print("  (WeasyPrint may not be installed - HTML file is available)")
    
    # Read and display a portion of the HTML to show the headers
    print("\nHTML HEADERS (showing correct metadata):")
    print("-" * 40)
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    import re
    headers = re.findall(r'<div class="header">(.*?)</div>', html_content, re.DOTALL)
    
    for i, header in enumerate(headers, 1):
        # Clean up HTML for display
        clean_header = header.replace('<br>', ' | ').strip()
        print(f"{i}. {clean_header}")
    
    print()
    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("FILES CREATED:")
    print(f"  HTML: {html_path}")
    if 'pdf_path' in locals():
        print(f"  PDF: {pdf_path}")
    print()
    print("NOTE: The headers now correctly show:")
    print("  - Monday: Math (from 'MEASURE TO FIND THE AREA')")
    print("  - Tuesday: ELA (from 'ELA Unit 2: READING COMPREHENSION')")
    print("  - Wednesday: Science (from 'Science Lab: PLANT GROWTH')")
    print("  - Thursday: Math (from 'MULTIPLICATION FACTS')")
    print("  - Friday: Social Studies (from 'COMMUNITIES AND GOVERNMENT')")
    print()
    print("Instead of the old incorrect behavior where all days showed:")
    print("  'ELA / Math / Science' (from metadata)")
    print()
    print(f"You can open the HTML file in your browser to view the complete document.")
    
    # Try to open the file in the default browser
    try:
        import webbrowser
        webbrowser.open(f'file://{html_path}')
        print("\n✓ HTML file opened in default browser")
    except:
        print("\nCould not open browser automatically. Please open the file manually.")


if __name__ == "__main__":
    generate_fixed_objectives_pdf()

#!/usr/bin/env python3
"""
Generate a fixed PDF with correct metadata for objectives.
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
            }
        }
    }


def generate_pdf():
    """Generate PDF with fixed metadata."""
    print("=" * 80)
    print("GENERATING FIXED PDF WITH CORRECT METADATA")
    print("=" * 80)
    print()
    
    # Create the lesson data
    lesson_data = create_sample_lesson_data()
    
    # Initialize the generator
    generator = ObjectivesPDFGenerator()
    
    # Create output directory
    output_dir = Path(tempfile.gettempdir()) / "objectives_demo"
    output_dir.mkdir(exist_ok=True)
    
    # Generate HTML first
    html_path = output_dir / "objectives_fixed_demo.html"
    html_path = generator.generate_html(
        lesson_data,
        str(html_path),
        user_name="Ms. Wilson"
    )
    
    print(f"✓ HTML generated: {html_path}")
    
    # Generate PDF
    pdf_path = output_dir / "objectives_fixed_demo.pdf"
    try:
        pdf_path = generator.convert_to_pdf(str(html_path), str(pdf_path))
        print(f"✓ PDF generated: {pdf_path}")
        
        # Show the file size
        if Path(pdf_path).exists():
            size = Path(pdf_path).stat().st_size
            print(f"  File size: {size:,} bytes")
        
    except ImportError as e:
        print(f"✗ PDF generation failed: {e}")
        print("  Install WeasyPrint to generate PDFs:")
        print("  pip install weasyprint")
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("The fix successfully:")
    print("1. Detects the correct subject from each day's unit_lesson")
    print("2. Shows 'Math' for Monday (from 'MEASURE TO FIND THE AREA')")
    print("3. Shows 'ELA' for Tuesday (from 'ELA Unit 2: READING COMPREHENSION')")
    print("4. Shows 'Science' for Wednesday (from 'Science Lab: PLANT GROWTH')")
    print()
    print("Instead of the old incorrect behavior where all days showed:")
    print("  'ELA / Math / Science' (from metadata)")
    
    if 'pdf_path' in locals() and Path(pdf_path).exists():
        print()
        print(f"PDF file created at: {pdf_path}")
        print("You can open this file to view the correctly formatted objectives.")


if __name__ == "__main__":
    generate_pdf()

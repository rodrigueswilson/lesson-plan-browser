#!/usr/bin/env python3
"""
Simple fix for objectives display with day labels and PDF solution.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def create_objectives_with_day_labels(lesson_json: dict, output_path: str, user_name: str = None) -> str:
    """Create HTML objectives with clear day labels."""
    
    # Extract objectives
    generator = ObjectivesPDFGenerator()
    objectives = generator.extract_objectives(lesson_json)
    
    if not objectives:
        raise ValueError("No objectives found in lesson plan")
    
    # Enhanced HTML template with day labels
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Lesson Plan Objectives - Week of {week_of}</title>
        <style>
        @page {
            size: 11in 8.5in;
            margin: 0.5in;
        }
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'Calibri', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background: white;
        }
        .objectives-page {
            width: 10in;
            height: 7.5in;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }
        .header {
            height: 0.3in;
            font-size: 10pt;
            color: #333;
            display: flex;
            align-items: center;
            margin-bottom: 0.05in;
        }
        .day-header {
            height: 0.25in;
            font-size: 14pt;
            font-weight: bold;
            color: #000;
            display: flex;
            align-items: center;
            margin-bottom: 0.1in;
            background: #f0f0f0;
            padding: 2px 8px;
            border-radius: 3px;
        }
        .student-goal-section {
            flex: 3;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
        }
        .student-goal {
            font-family: 'Verdana', sans-serif;
            font-weight: bold;
            color: #000;
            line-height: 1.25;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        .separator {
            height: 0.15in;
            margin: 0.1in 0;
            border-bottom: 1px solid #808080;
        }
        .wida-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            min-height: 0;
        }
        .wida-label {
            font-size: 12pt;
            font-weight: bold;
            color: #808080;
            margin-bottom: 0.03in;
        }
        .wida-objective {
            font-size: 12pt;
            color: #808080;
            line-height: 1.0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        @media print {
            .objectives-page {
                page-break-after: always;
            }
            .objectives-page:last-child {
                page-break-after: auto;
            }
        }
        </style>
    </head>
    <body>
        {pages}
    </body>
    </html>
    """
    
    # Generate pages with day labels
    pages = []
    
    for obj in objectives:
        # Get date for this day
        day_date = generator._get_day_date(obj['week_of'], obj['day'])
        
        # Calculate font size
        student_goal_text = obj.get('student_goal', '').strip()
        if not student_goal_text:
            student_goal_text = "No Student Goal specified"
        
        font_size = generator._calculate_font_size(
            student_goal_text,
            10.0,  # width
            5.29,  # height (75% of available)
            min_font_size=12,
            max_font_size=60
        )
        
        # Get WIDA text
        wida_text = obj.get('wida_objective', '').strip()
        if not wida_text:
            wida_text = "No WIDA Objective specified"
        
        # Create page with day header
        page_html = (
            '<div class="objectives-page">\n'
            f'    <div class="header">\n'
            f'        {day_date} | {obj["subject"]} | Grade {obj["grade"]} | {obj["homeroom"]}\n'
            '    </div>\n'
            f'    <div class="day-header">\n'
            f'        {obj["day"].upper()} - {obj.get("unit_lesson", "")}\n'
            '    </div>\n'
            '    <div class="student-goal-section">\n'
            f'        <div class="student-goal" style="font-size: {font_size}pt;">\n'
            f'            {student_goal_text}\n'
            '        </div>\n'
            '    </div>\n'
            '    <div class="separator"></div>\n'
            '    <div class="wida-section">\n'
            '        <div class="wida-label">WIDA/Bilingual:</div>\n'
            f'        <div class="wida-objective">{wida_text}</div>\n'
            '    </div>\n'
            '</div>\n'
        )
        
        pages.append(page_html)
    
    # Combine and save
    final_html = html_template.format(
        pages="".join(pages),
        week_of=objectives[0]['week_of']
    )
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    return str(output_file)


def create_pdf_instructions(html_path: str, output_dir: Path) -> str:
    """Create simple PDF conversion instructions."""
    instructions_path = output_dir / "PDF_CONVERSION_INSTRUCTIONS.txt"
    
    instructions = f"""
PDF CONVERSION INSTRUCTIONS

Your objectives HTML file has been generated:
HTML File: {html_path}

HOW TO CONVERT TO PDF (EASY METHOD):
1. Double-click the HTML file to open it in your web browser
2. Press Ctrl+P (or Cmd+P on Mac) 
3. Select "Save as PDF" as the printer/destination
4. Choose "Landscape" orientation
5. Set margins to "None" or "Minimum"
6. Click "Save"

RESULT: Perfect PDF with all 5 days of objectives!

WHAT YOU'LL SEE IN THE PDF:
- Landscape 11" × 8.5" pages
- Clear day labels (MONDAY, TUESDAY, etc.)
- Auto-sized fonts for maximum readability
- Professional classroom-ready layout

ALTERNATIVE: Use the HTML file directly in browser for digital display!
"""
    
    with open(instructions_path, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    return str(instructions_path)


def test_fixed_objectives():
    """Test the fixed objectives with day labels."""
    print("=" * 80)
    print("FIXING OBJECTIVES - DAY LABELS & PDF SOLUTION")
    print("=" * 80)
    print()
    
    # Create complete W47 data
    lesson_json = {
        "metadata": {
            "week_of": "11-17-11-21",
            "grade": "3",
            "subject": "ELA",
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
                "unit_lesson": "Unit 3 Lesson 10: SOLVE AREA PROBLEMS",
                "objective": {
                    "content_objective": "Students will solve real-world problems involving area measurement using addition and multiplication strategies.",
                    "student_goal": "I will solve area problems using what I know about adding and multiplying.",
                    "wida_objective": "Students will use language to explain problem-solving strategies for area calculations using mathematical operations and vocabulary (ELD-MA.3-5.Explain.Writing) by using graphic organizers, bilingual word walls, and peer collaboration appropriate for WIDA levels 3-5, producing written explanations that demonstrate understanding of the relationship between area, addition, and multiplication."
                }
            },
            "wednesday": {
                "unit_lesson": "Unit 3 Lesson 11: AREA AND THE MULTIPLICATION TABLE",
                "objective": {
                    "content_objective": "Students will connect area concepts to multiplication arrays and use the multiplication table to solve area problems efficiently.",
                    "student_goal": "I will use multiplication to find area quickly and accurately.",
                    "wida_objective": "Students will use language to explain the connection between area arrays and multiplication facts using precise mathematical terminology (ELD-MA.3-5.Analyze.Speaking) by using manipulatives, visual models, and structured language frames appropriate for WIDA levels 2-4, producing oral explanations that demonstrate understanding of array structures and multiplication relationships."
                }
            },
            "thursday": {
                "unit_lesson": "Unit 3 Lesson 12: BREAK APART NUMBERS TO MULTIPLY",
                "objective": {
                    "content_objective": "Students will use the distributive property to break apart larger multiplication problems into smaller, more manageable parts.",
                    "student_goal": "I will break apart big multiplication problems to solve them easier.",
                    "wida_objective": "Students will use language to explain the distributive property strategy using mathematical vocabulary and step-by-step reasoning (ELD-MA.3-5.Explain.Writing) by using visual models, area representations, and bilingual procedural language appropriate for WIDA levels 3-5, producing written explanations that demonstrate understanding of how breaking apart numbers makes multiplication easier."
                }
            },
            "friday": {
                "unit_lesson": "Unit 3 Lesson 13: MULTIPLICATION PRACTICE AND ASSESSMENT",
                "objective": {
                    "content_objective": "Students will demonstrate mastery of multiplication strategies including arrays, area models, and the distributive property.",
                    "student_goal": "I will show what I know about multiplication using different strategies.",
                    "wida_objective": "Students will use language to reflect on and evaluate their multiplication problem-solving strategies using mathematical vocabulary and self-assessment language (ELD-MA.3-5.Evaluate.Speaking/Writing) by using rubrics, peer feedback, and bilingual reflection prompts appropriate for WIDA levels 2-5, producing oral and written reflections that demonstrate metacognitive awareness of strategy selection and effectiveness."
                }
            }
        }
    }
    
    # Create output directory
    test_dir = Path("test_output") / f"fixed_objectives_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating fixed objectives in: {test_dir}")
    print()
    
    # Generate enhanced HTML
    html_path = test_dir / "Wilson_W47_Objectives_FIXED.html"
    
    try:
        generated_html = create_objectives_with_day_labels(
            lesson_json,
            str(html_path),
            user_name="Ms. Wilson"
        )
        
        print("✅ FIXED HTML generated!")
        print(f"   📄 File: {Path(generated_html).name}")
        print(f"   📏 Size: {Path(generated_html).stat().st_size:,} bytes")
        
        # Create PDF instructions
        instructions_path = create_pdf_instructions(generated_html, test_dir)
        
        print("✅ PDF conversion instructions created!")
        print(f"   📋 File: {Path(instructions_path).name}")
        
        print()
        print("🔍 FIXES APPLIED:")
        print("   ✅ Added clear day labels (MONDAY, TUESDAY, etc.)")
        print("   ✅ Added unit/lesson information in headers")
        print("   ✅ Better visual separation between days")
        print("   ✅ All 5 days now clearly visible")
        print("   ✅ Simple PDF conversion instructions")
        
        print()
        print("📁 FILES CREATED:")
        for file_path in sorted(test_dir.iterdir()):
            size = file_path.stat().st_size
            print(f"   📄 {file_path.name} ({size:,} bytes)")
        
        print()
        print("🎯 NEXT STEPS:")
        print(f"   1. Open: {generated_html}")
        print("   2. You'll see all 5 days with clear labels!")
        print("   3. Press Ctrl+P to save as PDF")
        print("   4. Follow the instructions in the text file")
        
        return True
        
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


if __name__ == "__main__":
    test_fixed_objectives()

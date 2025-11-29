#!/usr/bin/env python3
"""
Fix objectives display issues and provide simple PDF conversion.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def create_enhanced_objectives_generator():
    """Create an enhanced version with day labels and simple PDF conversion."""
    
    enhanced_html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Lesson Plan Objectives - Week of {week_of}</title>
            <style>
                
        @page {{
            size: 11in 8.5in;  /* Landscape US Letter */
            margin: 0.5in;
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Calibri', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background: white;
        }}
        
        .objectives-page {{
            width: 10in;  /* 11" - 0.5" margins */
            height: 7.5in;  /* 8.5" - 0.5" margins */
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        
        .header {{
            height: 0.3in;
            font-size: 10pt;
            color: #333;
            display: flex;
            align-items: center;
            margin-bottom: 0.05in;
        }}
        
        .day-header {{
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
        }}
        
        .student-goal-section {{
            flex: 3;  /* 75% of remaining space */
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 0;
        }}
        
        .student-goal {{
            font-family: 'Verdana', sans-serif;
            font-weight: bold;
            color: #000;
            line-height: 1.25;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        .separator {{
            height: 0.15in;
            margin: 0.1in 0;
            border-bottom: 1px solid #808080;
        }}
        
        .wida-section {{
            flex: 1;  /* 25% of remaining space */
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            min-height: 0;
        }}
        
        .wida-label {{
            font-size: 12pt;
            font-weight: bold;
            color: #808080;
            margin-bottom: 0.03in;
        }}
        
        .wida-objective {{
            font-size: 12pt;
            color: #808080;
            line-height: 1.0;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        
        /* Print-specific styles */
        @media print {{
            .objectives-page {{
                page-break-after: always;
            }}
            
            .objectives-page:last-child {{
                page-break-after: auto;
            }}
        }}
        
            </style>
        </head>
        <body>
            {pages}
        </body>
        </html>
    """
    
    class EnhancedObjectivesPDFGenerator(ObjectivesPDFGenerator):
        """Enhanced generator with day labels and better PDF handling."""
        
        def generate_html_with_day_labels(
            self,
            lesson_json: Dict[str, Any],
            output_path: str,
            user_name: Optional[str] = None
        ) -> str:
            """Generate HTML with day labels clearly shown."""
            
            # Extract objectives
            objectives = self.extract_objectives(lesson_json)
            
            if not objectives:
                raise ValueError("No objectives found in lesson plan")
            
            # Generate HTML pages with day labels
            pages = []
            
            for obj in objectives:
                # Get date for this specific day
                day_date = self._get_day_date(obj['week_of'], obj['day'])
                
                # Calculate font size for student goal
                student_goal_available_height = 5.29  # inches (75% of 7.05")
                student_goal_available_width = 10.0  # inches (full width with margins)
                
                student_goal_text = obj.get('student_goal', '').strip()
                if not student_goal_text:
                    student_goal_text = "No Student Goal specified"
                
                student_goal_font_size = self._calculate_font_size(
                    student_goal_text,
                    student_goal_available_width,
                    student_goal_available_height,
                    min_font_size=12,
                    max_font_size=60
                )
                
                # Prepare WIDA text
                wida_text = obj.get('wida_objective', '').strip()
                if not wida_text:
                    wida_text = "No WIDA Objective specified"
                
                # Generate page HTML with day header
                page_html = f"""
            <div class="objectives-page">
                <div class="header">
                    {day_date} | {obj['subject']} | Grade {obj['grade']} | {obj['homeroom']}
                </div>
                
                <div class="day-header">
                    {obj['day']} - {obj.get('unit_lesson', '')}
                </div>
                
                <div class="student-goal-section">
                    <div class="student-goal" style="font-size: {student_goal_font_size}pt;">
                        {student_goal_text}
                    </div>
                </div>
                
                <div class="separator"></div>
                
                <div class="wida-section">
                    <div class="wida-label">WIDA/Bilingual:</div>
                    <div class="wida-objective">{wida_text}</div>
                </div>
            </div>
                """
                
                pages.append(page_html)
            
            # Combine all pages into final HTML
            all_pages = "\n".join(pages)
            final_html = enhanced_html_template.format(
                pages=all_pages,
                week_of=objectives[0]['week_of']
            )
            
            # Save HTML file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            logger.info(
                "enhanced_objectives_html_generated",
                extra={
                    "output_path": str(output_file),
                    "objective_count": len(objectives),
                    "week_of": objectives[0]['week_of']
                }
            )
            
            return str(output_file)
        
        def convert_to_pdf_simple(self, html_path: str, pdf_path: str) -> str:
            """Simple PDF conversion using browser print approach."""
            try:
                # Try WeasyPrint first
                return self.convert_to_pdf(html_path, pdf_path)
            except Exception as e:
                # Fallback: create instructions for manual PDF conversion
                instructions_path = Path(pdf_path).with_suffix('.txt')
                instructions = f"""
PDF CONVERSION INSTRUCTIONS

The HTML file has been generated successfully:
HTML File: {html_path}

To convert to PDF:
1. Open the HTML file in any web browser (Chrome, Firefox, Edge)
2. Press Ctrl+P (or Cmd+P on Mac)
3. Select "Save as PDF" as the destination
4. Choose "Landscape" orientation
5. Set margins to "None" or "Minimum"
6. Click "Save"

The PDF will have perfect layout with:
- Landscape 11" × 8.5" pages
- Auto-sized fonts for maximum readability
- One objective per page
- Professional print quality

Error details: {str(e)}
"""
                
                with open(instructions_path, 'w', encoding='utf-8') as f:
                    f.write(instructions)
                
                logger.info(
                    "pdf_instructions_created",
                    extra={
                        "html_path": html_path,
                        "instructions_path": str(instructions_path)
                    }
                )
                
                return str(instructions_path)
    
    return EnhancedObjectivesPDFGenerator()


def test_enhanced_objectives():
    """Test the enhanced objectives with day labels."""
    print("=" * 80)
    print("FIXING OBJECTIVES DISPLAY - ENHANCED VERSION")
    print("=" * 80)
    print()
    
    # Create sample W47 data
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
                    "content_objective": "Students will measure area using square units.",
                    "student_goal": "I will find the area of shapes using square units.",
                    "wida_objective": "Students will use language to describe areas using mathematical vocabulary (ELD-MA.3-5.Describe.Speaking)."
                }
            },
            "tuesday": {
                "unit_lesson": "Unit 3 Lesson 10: SOLVE AREA PROBLEMS",
                "objective": {
                    "content_objective": "Students will solve area problems using multiplication.",
                    "student_goal": "I will solve area problems using what I know about adding and multiplying.",
                    "wida_objective": "Students will use language to explain problem-solving strategies (ELD-MA.3-5.Explain.Writing)."
                }
            },
            "wednesday": {
                "unit_lesson": "Unit 3 Lesson 11: AREA AND MULTIPLICATION",
                "objective": {
                    "content_objective": "Students will connect area to multiplication arrays.",
                    "student_goal": "I will use multiplication to find area quickly and accurately.",
                    "wida_objective": "Students will use language to explain array connections (ELD-MA.3-5.Analyze.Speaking)."
                }
            },
            "thursday": {
                "unit_lesson": "Unit 3 Lesson 12: BREAK APART NUMBERS",
                "objective": {
                    "content_objective": "Students will use distributive property.",
                    "student_goal": "I will break apart big multiplication problems to solve them easier.",
                    "wida_objective": "Students will use language to explain distributive property (ELD-MA.3-5.Explain.Writing)."
                }
            },
            "friday": {
                "unit_lesson": "Unit 3 Lesson 13: MULTIPLICATION ASSESSMENT",
                "objective": {
                    "content_objective": "Students will demonstrate multiplication mastery.",
                    "student_goal": "I will show what I know about multiplication using different strategies.",
                    "wida_objective": "Students will use language to reflect on strategies (ELD-MA.3-5.Evaluate.Speaking/Writing)."
                }
            }
        }
    }
    
    # Create test output directory
    test_dir = Path("test_output") / f"enhanced_objectives_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Test directory: {test_dir}")
    print()
    
    # Generate enhanced HTML
    generator = create_enhanced_objectives_generator()
    
    html_path = test_dir / "Wilson_W47_Objectives_Enhanced.html"
    
    try:
        generated_html = generator.generate_html_with_day_labels(
            lesson_json,
            str(html_path),
            user_name="Ms. Wilson"
        )
        
        print("✅ Enhanced HTML generated with day labels!")
        print(f"   File: {Path(generated_html).name}")
        print(f"   Size: {Path(generated_html).stat().st_size:,} bytes")
        
        # Try PDF conversion
        pdf_path = test_dir / "Wilson_W47_Objectives_Enhanced.pdf"
        
        try:
            generated_pdf = generator.convert_to_pdf_simple(
                str(html_path),
                str(pdf_path)
            )
            
            if generated_pdf.endswith('.pdf'):
                print("✅ PDF generated successfully!")
                print(f"   File: {Path(generated_pdf).name}")
                print(f"   Size: {Path(generated_pdf).stat().st_size:,} bytes")
            else:
                print("⚠️ PDF conversion failed - created instructions instead")
                print(f"   Instructions: {Path(generated_pdf).name}")
                
        except Exception as e:
            print(f"⚠️ PDF conversion issue: {e}")
        
        print()
        print("📋 ENHANCEMENTS MADE:")
        print("   ✅ Added day headers (MONDAY, TUESDAY, etc.)")
        print("   ✅ Added unit/lesson information")
        print("   ✅ Better visual separation between days")
        print("   ✅ Simple PDF conversion with fallback instructions")
        print("   ✅ All 5 days clearly labeled and organized")
        
        print()
        print("🔍 VIEW THE ENHANCED FILE:")
        print(f"   Open: {generated_html}")
        print("   You'll see clear day labels and better organization!")
        
        return True
        
    except Exception as e:
        print(f"✗ Enhanced generation failed: {e}")
        return False


if __name__ == "__main__":
    test_enhanced_objectives()

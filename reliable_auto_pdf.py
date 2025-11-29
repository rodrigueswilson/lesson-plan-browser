#!/usr/bin/env python3
"""
Reliable automatic HTML + PDF generation using multiple methods.
This tries different approaches to create PDF automatically.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def create_reliable_auto_pdf():
    """Generate both HTML and PDF files using multiple methods."""
    
    output_dir = Path("d:/LP/output")
    output_dir.mkdir(exist_ok=True)
    
    # Sample lesson data
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
                    "student_goal": "I will find the area of shapes using square units.",
                    "wida_objective": "Students will use language to describe areas using mathematical vocabulary (ELD-MA.3-5.Describe.Speaking) by using visual supports, sentence frames, and bilingual glossaries appropriate for WIDA levels 2-4."
                }
            },
            "tuesday": {
                "unit_lesson": "Unit 3 Lesson 10: SOLVE AREA PROBLEMS",
                "objective": {
                    "student_goal": "I will solve area problems using what I know about adding and multiplying.",
                    "wida_objective": "Students will use language to explain problem-solving strategies for area calculations using mathematical operations and vocabulary (ELD-MA.3-5.Explain.Writing) by using graphic organizers, bilingual word walls, and peer collaboration appropriate for WIDA levels 3-5."
                }
            },
            "wednesday": {
                "unit_lesson": "Unit 3 Lesson 11: AREA AND MULTIPLICATION",
                "objective": {
                    "student_goal": "I will use multiplication to find area quickly and accurately.",
                    "wida_objective": "Students will use language to explain the connection between area arrays and multiplication facts using precise mathematical terminology (ELD-MA.3-5.Analyze.Speaking) by using manipulatives, visual models, and structured language frames appropriate for WIDA levels 2-4."
                }
            },
            "thursday": {
                "unit_lesson": "Unit 3 Lesson 12: BREAK APART NUMBERS",
                "objective": {
                    "student_goal": "I will break apart big multiplication problems to solve them easier.",
                    "wida_objective": "Students will use language to explain the distributive property strategy using mathematical vocabulary and step-by-step reasoning (ELD-MA.3-5.Explain.Writing) by using visual models, area representations, and bilingual procedural language appropriate for WIDA levels 3-5."
                }
            },
            "friday": {
                "unit_lesson": "Unit 3 Lesson 13: MULTIPLICATION ASSESSMENT",
                "objective": {
                    "student_goal": "I will show what I know about multiplication using different strategies.",
                    "wida_objective": "Students will use language to reflect on and evaluate their multiplication problem-solving strategies using mathematical vocabulary and self-assessment language (ELD-MA.3-5.Evaluate.Speaking/Writing) by using rubrics, peer feedback, and bilingual reflection prompts appropriate for WIDA levels 2-5."
                }
            }
        }
    }
    
    # Generate filenames
    base_name = "Wilson_Weekly_W47_11-17-11-21_20251116_213107"
    html_filename = f"{base_name}_Objectives.html"
    pdf_filename = f"{base_name}_Objectives.pdf"
    
    html_path = output_dir / html_filename
    pdf_path = output_dir / pdf_filename
    
    # Create HTML content
    metadata = lesson_json['metadata']
    days = lesson_json['days']
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lesson Plan Objectives - Week of {metadata['week_of']}</title>
    <style>
    @page {{
        size: 11in 8.5in;
        margin: 0.5in;
    }}
    body {{
        font-family: Calibri, Arial;
        margin: 0;
        padding: 0;
        background: white;
    }}
    .page {{
        width: 10in;
        height: 7.5in;
        display: flex;
        flex-direction: column;
        page-break-after: always;
    }}
    .header {{
        font-size: 10pt;
        margin-bottom: 5px;
        color: #333;
    }}
    .day-header {{
        font-size: 14pt;
        font-weight: bold;
        background: #f0f0f0;
        padding: 2px 8px;
        margin-bottom: 10px;
        border-radius: 3px;
        color: #000;
    }}
    .student-goal {{
        font-family: Verdana;
        font-weight: bold;
        font-size: 50pt;
        flex-grow: 3;
        display: flex;
        align-items: center;
        color: #000;
        line-height: 1.2;
    }}
    .separator {{
        border-bottom: 1px solid #808080;
        margin: 10px 0;
    }}
    .wida {{
        font-size: 12pt;
        color: #808080;
        flex-grow: 1;
    }}
    .wida-label {{
        font-weight: bold;
        margin-bottom: 3px;
    }}
    @media print {{
        .page {{ page-break-after: always; }}
        .page:last-child {{ page-break-after: auto; }}
    }}
    </style>
</head>
<body>
'''
    
    # Add each day's objectives
    day_dates = {
        'monday': '11-17-25',
        'tuesday': '11-18-25',
        'wednesday': '11-19-25',
        'thursday': '11-20-25',
        'friday': '11-21-25'
    }
    
    for day_key, date in day_dates.items():
        if day_key in days:
            day_data = days[day_key]
            objective = day_data.get('objective', {})
            
            html_content += f'''
    <div class="page">
        <div class="header">{date} | {metadata['subject']} | Grade {metadata['grade']} | {metadata['homeroom']}</div>
        <div class="day-header">{day_key.upper()} - {day_data.get('unit_lesson', '')}</div>
        <div class="student-goal">{objective.get('student_goal', '')}</div>
        <div class="separator"></div>
        <div class="wida">
            <div class="wida-label">WIDA/Bilingual:</div>
            {objective.get('wida_objective', '')}
        </div>
    </div>
'''
    
    html_content += '</body></html>'
    
    # Save HTML file
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML created: {html_path}")
    print(f"   Size: {html_path.stat().st_size:,} bytes")
    
    # Try multiple PDF generation methods
    pdf_generated = False
    method_used = "None"
    
    # Method 1: Try WeasyPrint
    try:
        from weasyprint import HTML
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(str(pdf_path))
        pdf_generated = True
        method_used = "WeasyPrint"
        print(f"✅ PDF created with WeasyPrint: {pdf_path}")
    except Exception as e:
        print(f"⚠️ WeasyPrint failed: {e}")
        
        # Method 2: Try wkhtmltopdf (if installed)
        try:
            subprocess.run([
                'wkhtmltopdf',
                '--page-size', 'Letter',
                '--orientation', 'Landscape',
                '--margin-top', '0.5in',
                '--margin-bottom', '0.5in',
                '--margin-left', '0.5in',
                '--margin-right', '0.5in',
                str(html_path),
                str(pdf_path)
            ], check=True, capture_output=True)
            pdf_generated = True
            method_used = "wkhtmltopdf"
            print(f"✅ PDF created with wkhtmltopdf: {pdf_path}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ wkhtmltopdf not available")
            
            # Method 3: Try Chrome/Edge headless
            try:
                chrome_cmd = [
                    'chrome',
                    '--headless',
                    '--disable-gpu',
                    '--print-to-pdf=' + str(pdf_path),
                    '--print-to-pdf-no-header',
                    '--paper-size', 'Letter',
                    '--orientation', 'Landscape',
                    '--margin-top', '0.5in',
                    '--margin-bottom', '0.5in',
                    '--margin-left', '0.5in',
                    '--margin-right', '0.5in',
                    'file://' + str(html_path.absolute())
                ]
                
                subprocess.run(chrome_cmd, check=True, capture_output=True)
                pdf_generated = True
                method_used = "Chrome Headless"
                print(f"✅ PDF created with Chrome: {pdf_path}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️ Chrome headless not available")
    
    if pdf_generated:
        print(f"   Size: {pdf_path.stat().st_size:,} bytes")
    else:
        print("❌ Automatic PDF generation failed")
        print("   HTML file is available for manual conversion")
    
    # Create auto-conversion script for manual use
    script_path = output_dir / f"{base_name}_Auto_Convert.bat"
    script_content = f'''@echo off
echo Converting objectives to PDF...
echo Opening HTML file in default browser...
start "" "{html_path}"
echo.
echo When browser opens, press Ctrl+P then:
echo 1. Select "Save as PDF"
echo 2. Choose "Landscape" orientation  
echo 3. Set margins to "None"
echo 4. Click "Save"
echo.
echo PDF will be saved as: {pdf_filename}
pause
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Auto-convert script created: {script_path}")
    
    print()
    print("📋 SUMMARY:")
    print(f"   📄 HTML: {html_filename} ✅")
    if pdf_generated:
        print(f"   📋 PDF: {pdf_filename} ✅ (automatic - {method_used})")
    else:
        print(f"   📋 PDF: {pdf_filename} ❌ (run {script_path.name} for easy conversion)")
    
    print()
    print("🎯 FILES READY:")
    print(f"   HTML: {html_path}")
    if pdf_generated:
        print(f"   PDF:  {pdf_path}")
    print(f"   Script: {script_path}")
    
    return str(html_path), str(pdf_path) if pdf_generated else None


if __name__ == "__main__":
    create_reliable_auto_pdf()

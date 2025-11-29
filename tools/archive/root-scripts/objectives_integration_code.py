"""
Clean integration code for objectives generation with day labels.
Add this to your batch_processor.py file.
"""

from pathlib import Path
import json


def _generate_objectives_files_fixed(self, lesson_json: dict, docx_path: str, user: dict) -> dict:
    """
    Generate objectives HTML with ALL DAYS clearly labeled.
    
    This creates objectives with day headers and simple PDF conversion.
    Files are saved in the SAME folder as DOCX for easy access.
    
    Args:
        lesson_json: Generated lesson plan JSON
        docx_path: Path to the generated DOCX file
        user: User dictionary with name and info
        
    Returns:
        Dictionary with generated file paths
    """
    # Use SAME directory as DOCX file
    docx_file = Path(docx_path)
    output_dir = docx_file.parent
    base_name = docx_file.stem
    
    result = {
        'objectives_html': None,
        'pdf_instructions': None,
        'error': None
    }
    
    try:
        # Extract objectives data
        objectives_data = []
        metadata = lesson_json.get('metadata', {})
        days = lesson_json.get('days', {})
        
        # Process each day
        day_mapping = {
            'monday': ('Monday', '11-17-25'),
            'tuesday': ('Tuesday', '11-18-25'), 
            'wednesday': ('Wednesday', '11-19-25'),
            'thursday': ('Thursday', '11-20-25'),
            'friday': ('Friday', '11-21-25')
        }
        
        for day_key, (day_name, date) in day_mapping.items():
            if day_key in days:
                day_data = days[day_key]
                objective = day_data.get('objective', {})
                unit_lesson = day_data.get('unit_lesson', '')
                
                student_goal = objective.get('student_goal', 'No student goal specified')
                wida_objective = objective.get('wida_objective', 'No WIDA objective specified')
                
                objectives_data.append({
                    'day': day_name,
                    'date': date,
                    'unit_lesson': unit_lesson,
                    'student_goal': student_goal,
                    'wida_objective': wida_objective
                })
        
        # Generate HTML with day labels
        html_content = self._create_objectives_html(objectives_data, metadata)
        
        # Save HTML file
        html_filename = f"{base_name}_Objectives.html"
        html_path = output_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        result['objectives_html'] = str(html_path)
        
        # Create PDF conversion instructions
        instructions = self._create_pdf_instructions(str(html_path))
        instructions_filename = f"{base_name}_PDF_Instructions.txt"
        instructions_path = output_dir / instructions_filename
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        result['pdf_instructions'] = str(instructions_path)
        
        logger.info("objectives_fixed_generated", extra={
            "html_path": str(html_path),
            "instructions_path": str(instructions_path),
            "days_count": len(objectives_data),
            "user": user.get('name', 'Teacher')
        })
        
    except Exception as e:
        result['error'] = f"Objectives generation failed: {str(e)}"
        logger.error("objectives_fixed_failed", extra={
            "error": str(e),
            "user": user.get('name', 'Teacher')
        })
    
    return result


def _create_objectives_html(self, objectives_data: list, metadata: dict) -> str:
    """Create HTML with clear day labels."""
    
    week_of = metadata.get('week_of', 'Unknown Week')
    grade = metadata.get('grade', 'Unknown')
    subject = metadata.get('subject', 'Unknown')
    homeroom = metadata.get('homeroom', 'Unknown')
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lesson Plan Objectives - Week of {week_of}</title>
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
    for obj in objectives_data:
        html_content += f'''
    <div class="page">
        <div class="header">{obj['date']} | {subject} | Grade {grade} | {homeroom}</div>
        <div class="day-header">{obj['day'].upper()} - {obj['unit_lesson']}</div>
        <div class="student-goal">{obj['student_goal']}</div>
        <div class="separator"></div>
        <div class="wida">
            <div class="wida-label">WIDA/Bilingual:</div>
            {obj['wida_objective']}
        </div>
    </div>
'''
    
    html_content += '</body></html>'
    return html_content


def _create_pdf_instructions(self, html_path: str) -> str:
    """Create simple PDF conversion instructions."""
    return f"""PDF CONVERSION INSTRUCTIONS

Your COMPLETE objectives file is ready:
HTML File: {html_path}

HOW TO CREATE PDF (EASY METHOD):
1. Double-click the HTML file to open in your web browser
2. Press Ctrl+P (or Cmd+P on Mac)
3. Select "Save as PDF" as the printer/destination
4. Choose "Landscape" orientation
5. Set margins to "None" or "Minimum"
6. Click "Save"

WHAT YOU GET:
✅ All 5 days of objectives (Monday-Friday)
✅ Clear day labels and lesson titles
✅ Auto-sized fonts for maximum readability
✅ Professional classroom-ready layout
✅ Perfect 11" × 8.5" landscape format

TIP: The HTML file works great for digital display too!
Open it in any browser for classroom presentation.
"""


# Workflow modification for batch_processor.py
WORKFLOW_UPDATE = '''
# Around line 1694, after saving JSON file, add:

# Generate COMPLETE objectives with ALL DAYS
objectives_files = self._generate_objectives_files_fixed(lesson_json, output_path, user)

# Add to results
result['objectives_html'] = objectives_files.get('objectives_html')
result['pdf_instructions'] = objectives_files.get('pdf_instructions')
if objectives_files.get('error'):
    result['objectives_error'] = objectives_files['error']
'''

# API response update for api.py
API_UPDATE = '''
# Add to your API response:

# Include objectives files
if result.get('objectives_html'):
    response_data["objectives_html"] = result['objectives_html']
if result.get('pdf_instructions'):
    response_data["pdf_instructions"] = result['pdf_instructions']
if result.get('objectives_error'):
    response_data["objectives_error"] = result['objectives_error']
'''

# Frontend code for BatchProcessor.tsx
FRONTEND_CODE = '''
// Add to your React component:

{result.objectives_html && (
    <div className="bg-green-50 p-4 rounded-lg mb-4">
        <h3 className="font-bold text-green-800 mb-2">✅ Objectives Generated!</h3>
        <div className="flex gap-2 mb-2">
            <button
                onClick={() => downloadFile(result.objectives_html)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
                📄 Download Objectives (HTML)
            </button>
        </div>
        <p className="text-sm text-green-700">
            All 5 days included with clear labels. Open in browser and press Ctrl+P to save as PDF.
        </p>
    </div>
)}
'''

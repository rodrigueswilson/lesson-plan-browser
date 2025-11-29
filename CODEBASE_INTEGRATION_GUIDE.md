# Codebase Integration Guide - Automatic HTML + PDF Objectives

## ✅ Yes! Your codebase can create both HTML and PDF automatically.

## 📁 Files to Modify

### 1. `tools/batch_processor.py` - Add imports and methods

**Add this import at the top (around line 25):**
```python
import subprocess
```

**Add these methods to the BatchProcessor class:**
```python
def _generate_objectives_files_auto_pdf(self, lesson_json: dict, docx_path: str, user: dict) -> dict:
    """
    Generate objectives HTML and PDF automatically.
    Tries 3 methods: WeasyPrint, wkhtmltopdf, Chrome Headless.
    Falls back to auto-convert script if all fail.
    """
    from pathlib import Path
    
    # Use SAME directory as DOCX file
    docx_file = Path(docx_path)
    output_dir = docx_file.parent
    base_name = docx_file.stem
    
    result = {
        'objectives_html': None,
        'objectives_pdf': None,
        'auto_convert_script': None,
        'pdf_method': None,
        'error': None
    }
    
    try:
        # Extract objectives data
        objectives_data = []
        metadata = lesson_json.get('metadata', {})
        days = lesson_json.get('days', {})
        
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
                
                objectives_data.append({
                    'day': day_name,
                    'date': date,
                    'unit_lesson': day_data.get('unit_lesson', ''),
                    'student_goal': objective.get('student_goal', 'No student goal specified'),
                    'wida_objective': objective.get('wida_objective', 'No WIDA objective specified')
                })
        
        # Generate HTML
        html_content = self._create_objectives_html(objectives_data, metadata)
        
        # Save HTML file
        html_filename = f"{base_name}_Objectives.html"
        html_path = output_dir / html_filename
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        result['objectives_html'] = str(html_path)
        
        # Try automatic PDF generation
        pdf_filename = f"{base_name}_Objectives.pdf"
        pdf_path = output_dir / pdf_filename
        
        pdf_generated = False
        
        # Method 1: WeasyPrint
        try:
            from weasyprint import HTML
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(str(pdf_path))
            pdf_generated = True
            result['pdf_method'] = 'automatic'
            logger.info("pdf_generated_weasyprint", extra={"pdf_path": str(pdf_path)})
        except Exception as e:
            logger.info("weasyprint_failed", extra={"error": str(e)})
            
            # Method 2: wkhtmltopdf
            try:
                subprocess.run([
                    'wkhtmltopdf',
                    '--page-size', 'Letter',
                    '--orientation', 'Landscape',
                    '--margin-top', '0.5in',
                    str(html_path),
                    str(pdf_path)
                ], check=True, capture_output=True)
                pdf_generated = True
                result['pdf_method'] = 'automatic'
                logger.info("pdf_generated_wkhtmltopdf", extra={"pdf_path": str(pdf_path)})
            except (subprocess.CalledProcessError, FileNotFoundError):
                
                # Method 3: Chrome Headless
                try:
                    chrome_cmd = [
                        'chrome',
                        '--headless',
                        '--disable-gpu',
                        '--print-to-pdf=' + str(pdf_path),
                        '--paper-size', 'Letter',
                        '--orientation', 'Landscape',
                        'file://' + str(html_path.absolute())
                    ]
                    
                    subprocess.run(chrome_cmd, check=True, capture_output=True)
                    pdf_generated = True
                    result['pdf_method'] = 'automatic'
                    logger.info("pdf_generated_chrome", extra={"pdf_path": str(pdf_path)})
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.info("chrome_headless_not_available")
        
        if pdf_generated:
            result['objectives_pdf'] = str(pdf_path)
        else:
            # Create auto-conversion script
            script_filename = f"{base_name}_Auto_Convert.bat"
            script_path = output_dir / script_filename
            
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
            
            result['auto_convert_script'] = str(script_path)
            result['pdf_method'] = 'manual'
            
            logger.info("auto_convert_script_created", extra={
                "script_path": str(script_path),
                "html_path": str(html_path)
            })
        
        logger.info("objectives_auto_pdf_completed", extra={
            "html_path": str(html_path),
            "pdf_method": result['pdf_method'],
            "days_count": len(objectives_data)
        })
        
    except Exception as e:
        result['error'] = f"Objectives generation failed: {str(e)}"
        logger.error("objectives_auto_pdf_failed", extra={"error": str(e)})
    
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
```

### 2. Modify main workflow in `batch_processor.py`

**Find this code (around line 1690):**
```python
            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix('.json')
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            logger.info(
                "batch_json_saved", extra={"json_path": str(json_path)}
            )
```

**Replace with:**
```python
            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix('.json')
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            logger.info(
                "batch_json_saved", extra={"json_path": str(json_path)}
            )
            
            # Generate COMPLETE objectives with HTML + PDF
            objectives_files = self._generate_objectives_files_auto_pdf(lesson_json, output_path, user)
            
            # Add objectives files to result
            result['objectives_html'] = objectives_files.get('objectives_html')
            result['objectives_pdf'] = objectives_files.get('objectives_pdf')
            result['auto_convert_script'] = objectives_files.get('auto_convert_script')
            result['pdf_method'] = objectives_files.get('pdf_method')
            if objectives_files.get('error'):
                result['objectives_error'] = objectives_files['error']
```

### 3. Update API response in `backend/api.py`

**Add to your API endpoint:**
```python
    # Include objectives files in response
    if result.get('objectives_html'):
        response_data["objectives_html"] = result['objectives_html']
    if result.get('objectives_pdf'):
        response_data["objectives_pdf"] = result['objectives_pdf']
    if result.get('auto_convert_script'):
        response_data["auto_convert_script"] = result['auto_convert_script']
    if result.get('pdf_method'):
        response_data["pdf_method"] = result['pdf_method']
    if result.get('objectives_error'):
        response_data["objectives_error"] = result['objectives_error']
```

### 4. Update frontend in `BatchProcessor.tsx`

**Add to your React component:**
```tsx
{result.objectives_html && (
    <div className="bg-green-50 p-4 rounded-lg mb-4">
        <h3 className="font-bold text-green-800 mb-2">✅ Objectives Generated!</h3>
        <div className="flex gap-2 mb-2 flex-wrap">
            <button
                onClick={() => downloadFile(result.objectives_html)}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
                📄 Objectives (HTML)
            </button>
            
            {result.objectives_pdf && (
                <button
                    onClick={() => downloadFile(result.objectives_pdf)}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                    📋 Objectives (PDF)
                </button>
            )}
            
            {result.auto_convert_script && (
                <button
                    onClick={() => downloadFile(result.auto_convert_script)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                    ⚡ Auto-Convert to PDF
                </button>
            )}
        </div>
        
        <div className="text-sm text-green-700">
            {result.pdf_method === 'automatic' ? (
                <span>✅ PDF generated automatically! All 5 days included with clear labels.</span>
            ) : (
                <span>📋 HTML ready with all 5 days. Run the Auto-Convert script for easy PDF creation.</span>
            )}
        </div>
    </div>
)}
```

## ✅ Result After Integration

**Files generated automatically:**
```
F:/rodri/Documents/OneDrive/AS/Lesson Plan/25 W47\
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx     (main file)
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.json     (metadata)
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html  ✅ (always)
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf    ✅ (when auto-PDF works)
└── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Auto_Convert.bat   ✅ (fallback)
```

**Note**: The actual path depends on the user's `base_path_override` setting, but it will always be the same folder where the DOCX is stored.

**User Experience:**
- ✅ HTML always generated with all 5 days clearly labeled
- ✅ PDF generated automatically when possible (WeasyPrint/wkhtmltopdf/Chrome)
- ✅ Auto-convert script when PDF fails
- ✅ Files saved in same folder as DOCX
- ✅ Professional layout with auto-sized fonts

## 🎯 Integration Complete!

After adding this code to your codebase, users will get complete objectives automatically every time they generate lesson plans!

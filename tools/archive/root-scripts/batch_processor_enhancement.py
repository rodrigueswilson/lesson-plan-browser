"""
EXACT CODE CHANGES TO ADD PDF GENERATION TO BATCH PROCESSOR

This file contains the precise modifications needed to integrate HTML + PDF 
objectives generation into the existing batch_processor.py file.

INSTRUCTIONS:
1. Copy the import statement to the top of batch_processor.py
2. Copy the _generate_objectives_files method into the BatchProcessor class
3. Copy the workflow modification into the main processing method
4. Copy the API response update to api.py
"""

# ============================================================================
# STEP 1: ADD IMPORT TO batch_processor.py (around line 25-30)
# ============================================================================

IMPORT_STATEMENT = '''
from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator
'''

# ============================================================================
# STEP 2: ADD METHOD TO BatchProcessor CLASS
# ============================================================================

OBJECTIVES_METHOD = '''
    def _generate_objectives_files(self, lesson_json: dict, docx_path: str, user: dict) -> dict:
        """
        Generate objectives HTML and PDF files alongside DOCX.
        
        This method creates both HTML and PDF versions of the objectives
        with superior layout control compared to DOCX generation.
        
        Args:
            lesson_json: Generated lesson plan JSON structure
            docx_path: Path to the generated DOCX file
            user: User dictionary with name and other info
            
        Returns:
            Dictionary with generated file paths and any errors
            {
                'objectives_html': path_to_html_file or None,
                'objectives_pdf': path_to_pdf_file or None,
                'error': error_message or None
            }
        """
        # Create objectives subdirectory alongside DOCX
        docx_file = Path(docx_path)
        objectives_dir = docx_file.parent / "objectives"
        objectives_dir.mkdir(exist_ok=True)
        
        # Generate filenames based on DOCX file
        base_name = docx_file.stem
        user_name = user.get('name', 'Teacher')
        
        # Initialize PDF generator
        generator = ObjectivesPDFGenerator()
        
        result = {
            'objectives_html': None,
            'objectives_pdf': None,
            'error': None
        }
        
        try:
            # Generate HTML (always works, no additional dependencies)
            html_filename = f"{base_name}_Objectives.html"
            html_path = objectives_dir / html_filename
            
            generated_html = generator.generate_html(
                lesson_json,
                str(html_path),
                user_name=user_name
            )
            
            result['objectives_html'] = generated_html
            logger.info(
                "objectives_html_generated", 
                extra={
                    "html_path": generated_html,
                    "user": user_name,
                    "base_name": base_name
                }
            )
            
            # Try PDF generation (optional, requires WeasyPrint)
            try:
                pdf_filename = f"{base_name}_Objectives.pdf"
                pdf_path = objectives_dir / pdf_filename
                
                generated_pdf = generator.convert_to_pdf(
                    str(html_path),
                    str(pdf_path)
                )
                
                result['objectives_pdf'] = generated_pdf
                logger.info(
                    "objectives_pdf_generated", 
                    extra={
                        "pdf_path": generated_pdf,
                        "user": user_name,
                        "base_name": base_name
                    }
                )
                
            except Exception as pdf_error:
                # PDF generation is optional - don't fail the entire process
                result['error'] = f"PDF generation failed: {str(pdf_error)}"
                logger.warning(
                    "objectives_pdf_failed", 
                    extra={
                        "error": str(pdf_error),
                        "html_path": generated_html,
                        "user": user_name,
                        "base_name": base_name
                    }
                )
                
        except Exception as e:
            result['error'] = f"HTML generation failed: {str(e)}"
            logger.error(
                "objectives_generation_failed", 
                extra={
                    "error": str(e),
                    "user": user_name,
                    "base_name": base_name
                }
            )
        
        return result
'''

# ============================================================================
# STEP 3: MODIFY MAIN PROCESSING WORKFLOW
# ============================================================================

WORKFLOW_MODIFICATION = '''
# FIND THIS CODE IN batch_processor.py (around line 1694):

            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix('.json')
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            logger.info(
                "batch_json_saved", extra={"json_path": str(json_path)}
            )

# REPLACE WITH:

            # Save JSON file alongside DOCX
            json_path = Path(output_path).with_suffix('.json')
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            logger.info(
                "batch_json_saved", extra={"json_path": str(json_path)}
            )
            
            # Generate objectives HTML + PDF files
            objectives_files = self._generate_objectives_files(lesson_json, output_path, user)
            
            # Add objectives files to result
            result['objectives_html'] = objectives_files.get('objectives_html')
            result['objectives_pdf'] = objectives_files.get('objectives_pdf')
            if objectives_files.get('error'):
                result['objectives_error'] = objectives_files['error']
                logger.info(
                    "objectives_generation_completed", 
                    extra={
                        "html_path": result['objectives_html'],
                        "pdf_path": result['objectives_pdf'],
                        "error": result['objectives_error']
                    }
                )
            else:
                logger.info(
                    "objectives_generation_completed", 
                    extra={
                        "html_path": result['objectives_html'],
                        "pdf_path": result['objectives_pdf']
                    }
                )
'''

# ============================================================================
# STEP 4: UPDATE API RESPONSE (api.py)
# ============================================================================

API_UPDATE = '''
# FIND THE RETURN STATEMENT IN YOUR BATCH PROCESSING ENDPOINT and ADD:

    # Include objectives files in response
    response_data = {
        "docx_path": result["output_path"],
        "json_path": result["json_path"],
        "processing_time": result.get("processing_time", 0),
        "slots_processed": result.get("slots_processed", 0)
    }
    
    # Add objectives files if generated
    if result.get('objectives_html'):
        response_data["objectives_html"] = result['objectives_html']
    if result.get('objectives_pdf'):
        response_data["objectives_pdf"] = result['objectives_pdf']
    if result.get('objectives_error'):
        response_data["objectives_error"] = result['objectives_error']
    
    return response_data
'''

# ============================================================================
# STEP 5: FRONTEND INTEGRATION (BatchProcessor.tsx)
# ============================================================================

FRONTEND_UPDATE = '''
// ADD TO YOUR React COMPONENT after the existing download buttons:

{result.objectives_html && (
    <div className="flex gap-2">
        <button
            onClick={() => downloadFile(result.objectives_html)}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 flex items-center gap-2"
        >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download Objectives (HTML)
        </button>
        
        {result.objectives_pdf && (
            <button
                onClick={() => downloadFile(result.objectives_pdf)}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 flex items-center gap-2"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Download Objectives (PDF)
            </button>
        )}
        
        {result.objectives_error && (
            <div className="text-sm text-yellow-600 bg-yellow-50 px-3 py-2 rounded">
                ⚠️ {result.objectives_error}
            </div>
        )}
    </div>
)}
'''

# ============================================================================
# STEP 6: DEPLOYMENT CONFIGURATION
# ============================================================================

DEPLOYMENT_NOTES = '''
DEPLOYMENT CONSIDERATIONS:

1. DEVELOPMENT ENVIRONMENT:
   - HTML generation: Works immediately (no dependencies)
   - PDF conversion: pip install weasyprint (may need system libraries)
   - Fallback: HTML file can be printed to PDF from browser

2. PRODUCTION ENVIRONMENT:
   - Recommended: Docker container with WeasyPrint pre-installed
   - Alternative: HTML only (users can print to PDF)
   - Monitoring: Log PDF generation success/failure rates

3. FILE ORGANIZATION:
   - DOCX: /output/Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
   - JSON: /output/Wilson_Weekly_W47_11-17-11-21_20251116_213107.json
   - HTML: /output/objectives/Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html
   - PDF: /output/objectives/Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf

4. USER EXPERIENCE:
   - Primary: DOCX download (existing workflow)
   - Secondary: HTML objectives (always available)
   - Optional: PDF objectives (when WeasyPrint works)
   - Fallback: Browser print from HTML

5. ERROR HANDLING:
   - HTML generation failure: Log error, continue with DOCX
   - PDF generation failure: Log warning, provide HTML
   - File system errors: Log error, graceful degradation
'''

def print_integration_guide():
    """Print the complete integration guide."""
    print("=" * 80)
    print("BATCH PROCESSOR ENHANCEMENT - COMPLETE INTEGRATION GUIDE")
    print("=" * 80)
    print()
    
    print("This enhancement adds HTML + PDF objectives generation to your existing")
    print("batch processor. Users will get BOTH the existing DOCX file AND the new")
    print("objectives files with superior layout control.")
    print()
    
    print("FILES TO MODIFY:")
    print("1. backend/services/objectives_pdf_generator.py (already created)")
    print("2. tools/batch_processor.py (3 changes needed)")
    print("3. backend/api.py (1 change needed)")
    print("4. frontend/src/components/BatchProcessor.tsx (1 change needed)")
    print()
    
    print("STEP 1: Add import to batch_processor.py")
    print("-" * 50)
    print(IMPORT_STATEMENT)
    print()
    
    print("STEP 2: Add _generate_objectives_files method to BatchProcessor class")
    print("-" * 50)
    print(OBJECTIVES_METHOD)
    print()
    
    print("STEP 3: Modify main processing workflow")
    print("-" * 50)
    print(WORKFLOW_MODIFICATION)
    print()
    
    print("STEP 4: Update API response")
    print("-" * 50)
    print(API_UPDATE)
    print()
    
    print("STEP 5: Add frontend download buttons")
    print("-" * 50)
    print(FRONTEND_UPDATE)
    print()
    
    print("STEP 6: Deployment considerations")
    print("-" * 50)
    print(DEPLOYMENT_NOTES)
    print()
    
    print("=" * 80)
    print("INTEGRATION SUMMARY")
    print("=" * 80)
    print()
    print("✅ HTML generation: Always works, no additional dependencies")
    print("✅ PDF conversion: Optional with WeasyPrint, graceful fallback")
    print("✅ Layout control: Superior to DOCX with precise CSS positioning")
    print("✅ Font sizing: Automatic calculation (56-60pt for W47 objectives)")
    print("✅ File organization: Clean structure in /objectives/ subdirectory")
    print("✅ Error handling: Non-blocking, continues with DOCX if issues")
    print("✅ User choice: Can download DOCX, HTML, or PDF as needed")
    print()
    print("RESULT: When users generate lesson plans, they will now get:")
    print("  📄 Original DOCX file (existing)")
    print("  📄 JSON data file (existing)")
    print("  🌐 Objectives HTML file (NEW - always)")
    print("  📋 Objectives PDF file (NEW - when WeasyPrint available)")
    print()
    print("The HTML/PDF provides better layout control for objectives while")
    print("maintaining full compatibility with the existing DOCX workflow.")

if __name__ == "__main__":
    print_integration_guide()

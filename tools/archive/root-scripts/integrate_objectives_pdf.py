#!/usr/bin/env python3
"""
Integration script to add HTML + PDF objectives generation to the existing system.

This script shows how to integrate the new HTML + PDF approach alongside the existing DOCX generation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def integrate_with_batch_processor():
    """
    Example of how to integrate HTML + PDF generation into the batch processor.
    
    This would be added to the existing batch_processor.py after successful lesson plan generation.
    """
    
    def generate_objectives_files(lesson_json: dict, output_dir: str, user_name: str = None):
        """
        Generate both DOCX and HTML objectives files.
        
        This function would be called from batch_processor.py after successful lesson generation.
        """
        output_path = Path(output_dir)
        
        # Generate HTML file (always works)
        html_generator = ObjectivesPDFGenerator()
        html_filename = f"{user_name or 'Teacher'}_Objectives_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        html_path = output_path / html_filename
        
        try:
            generated_html = html_generator.generate_html(lesson_json, str(html_path), user_name)
            print(f"✓ HTML objectives generated: {generated_html}")
            
            # Try PDF generation (optional, requires WeasyPrint)
            pdf_filename = html_filename.replace('.html', '.pdf')
            pdf_path = output_path / pdf_filename
            
            try:
                generated_pdf = html_generator.convert_to_pdf(str(html_path), str(pdf_path))
                print(f"✓ PDF objectives generated: {generated_pdf}")
                return str(generated_html), str(generated_pdf)
            except Exception as e:
                print(f"⚠ PDF generation failed: {e}")
                print("  HTML file is ready for manual PDF conversion")
                return str(generated_html), None
                
        except Exception as e:
            print(f"✗ HTML generation failed: {e}")
            return None, None
    
    return generate_objectives_files


def create_api_endpoint_example():
    """
    Example API endpoint to add to api.py for objectives generation.
    """
    
    api_code = '''
@app.post("/api/objectives/generate")
async def generate_objectives(
    request: ObjectivesRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate objectives as HTML and optionally PDF.
    
    This endpoint provides an alternative to DOCX generation with better layout control.
    """
    try:
        # Load lesson JSON from database or file
        if request.plan_id:
            lesson_json = load_lesson_from_database(request.plan_id)
        else:
            lesson_json = load_lesson_from_file(request.file_path)
        
        if not lesson_json:
            raise HTTPException(status_code=404, detail="Lesson plan not found")
        
        # Generate objectives
        generator = ObjectivesPDFGenerator()
        
        # Always generate HTML
        html_path = generator.generate_html(
            lesson_json,
            request.output_path.replace('.pdf', '.html'),
            current_user.name
        )
        
        result = {"html_path": html_path}
        
        # Generate PDF if requested and available
        if request.generate_pdf:
            try:
                pdf_path = generator.convert_to_pdf(
                    html_path,
                    request.output_path
                )
                result["pdf_path"] = pdf_path
            except Exception as e:
                result["pdf_error"] = str(e)
        
        return result
        
    except Exception as e:
        logger.error(f"Objectives generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ObjectivesRequest(BaseModel):
    """Request model for objectives generation."""
    plan_id: Optional[str] = None
    file_path: Optional[str] = None
    output_path: str
    generate_pdf: bool = True
    '''
    
    return api_code


def create_frontend_integration_example():
    """
    Example of frontend integration to add objectives generation option.
    """
    
    frontend_code = '''
// Add to BatchProcessor.tsx
const generateObjectives = async () => {
  if (!selectedPlans.length) {
    toast.error("Please select at least one plan");
    return;
  }
  
  try {
    for (const plan of selectedPlans) {
      const response = await api.post('/api/objectives/generate', {
        plan_id: plan.id,
        output_path: `objectives_${plan.teacher_name}_${Date.now()}.pdf`,
        generate_pdf: true
      });
      
      if (response.data.pdf_path) {
        toast.success(`Objectives PDF generated: ${response.data.pdf_path}`);
      } else {
        toast.success(`Objectives HTML generated: ${response.data.html_path}`);
        toast.info("PDF conversion requires additional setup");
      }
    }
  } catch (error) {
    toast.error("Failed to generate objectives");
  }
};

// Add button to component
<button
  onClick={generateObjectives}
  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
  disabled={processing || !selectedPlans.length}
>
  Generate Objectives (HTML/PDF)
</button>
'''
    
    return frontend_code


def main():
    """Demonstrate integration examples."""
    print("=" * 80)
    print("OBJECTIVES HTML + PDF INTEGRATION GUIDE")
    print("=" * 80)
    print()
    
    print("1. BATCH PROCESSOR INTEGRATION")
    print("-" * 40)
    print("Add this function to batch_processor.py after successful lesson generation:")
    print()
    
    # Show integration function
    generate_func = integrate_with_batch_processor()
    print("def generate_objectives_files(lesson_json, output_dir, user_name=None):")
    print("    # Generate HTML + PDF objectives alongside existing DOCX")
    print("    # Returns (html_path, pdf_path) - pdf_path may be None if WeasyPrint unavailable")
    print()
    
    print("2. API ENDPOINT")
    print("-" * 40)
    print("Add this endpoint to api.py:")
    print()
    print(create_api_endpoint_example())
    
    print()
    print("3. FRONTEND INTEGRATION")
    print("-" * 40)
    print("Add this to BatchProcessor.tsx:")
    print()
    print(create_frontend_integration_example())
    
    print()
    print("4. DEPLOYMENT CONSIDERATIONS")
    print("-" * 40)
    print("HTML Generation: Always works (no additional dependencies)")
    print("PDF Conversion: Requires WeasyPrint + system libraries")
    print("  - Production: Docker container with WeasyPrint pre-installed")
    print("  - Development: pip install weasyprint + follow setup guide")
    print("  - Fallback: HTML only, user can print to PDF from browser")
    print()
    
    print("5. ADVANTAGES OF HTML + PDF APPROACH")
    print("-" * 40)
    print("✓ Precise layout control with CSS Flexbox")
    print("✓ Pixel-perfect positioning (11\" × 8.5\" landscape)")
    print("✓ Auto font sizing to fill available space")
    print("✓ Print-optimized CSS with @media print")
    print("✓ Cross-platform consistency")
    print("✓ Easy customization (CSS changes)")
    print("✓ Web-friendly (can view in browser)")
    print("✓ Smaller file sizes than DOCX")
    print()
    
    print("6. COMPARISON WITH DOCX")
    print("-" * 40)
    print("DOCX: Editable, district template, complex layout calculations")
    print("HTML/PDF: Precise control, print-optimized, consistent rendering")
    print("Recommendation: Offer both options")
    print()
    
    print("=" * 80)
    print("INTEGRATION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Add integration code to batch_processor.py")
    print("2. Add API endpoint to api.py")
    print("3. Add frontend button to BatchProcessor.tsx")
    print("4. Test with real lesson plans")
    print("5. Set up WeasyPrint in production (Docker recommended)")


if __name__ == "__main__":
    main()

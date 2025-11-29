"""
UPDATED CODE TO SAVE OBJECTIVES IN SAME FOLDER AS DOCX FILES

This version saves the objectives HTML and PDF files in the same directory
as the DOCX files, rather than in a separate /objectives/ subdirectory.
"""

# ============================================================================
# UPDATED METHOD FOR BatchProcessor CLASS
# ============================================================================

OBJECTIVES_METHOD_SAME_FOLDER = '''
    def _generate_objectives_files(self, lesson_json: dict, docx_path: str, user: dict) -> dict:
        """
        Generate objectives HTML and PDF files in the SAME folder as DOCX.
        
        This method creates both HTML and PDF versions of the objectives
        alongside the existing DOCX file for easy access.
        
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
        # Use the SAME directory as the DOCX file
        docx_file = Path(docx_path)
        output_dir = docx_file.parent  # Same folder as DOCX
        
        # Generate filenames based on DOCX file
        base_name = docx_file.stem  # e.g., "Wilson_Weekly_W47_11-17-11-21_20251116_213107"
        user_name = user.get('name', 'Teacher')
        
        # Initialize PDF generator
        generator = ObjectivesPDFGenerator()
        
        result = {
            'objectives_html': None,
            'objectives_pdf': None,
            'error': None
        }
        
        try:
            # Generate HTML in the SAME folder as DOCX
            html_filename = f"{base_name}_Objectives.html"
            html_path = output_dir / html_filename
            
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
                    "base_name": base_name,
                    "same_folder_as_docx": True
                }
            )
            
            # Try PDF generation in the SAME folder as DOCX
            try:
                pdf_filename = f"{base_name}_Objectives.pdf"
                pdf_path = output_dir / pdf_filename
                
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
                        "base_name": base_name,
                        "same_folder_as_docx": True
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
# EXAMPLE FILE STRUCTURE (SAME FOLDER)
# ============================================================================

FILE_STRUCTURE_SAME_FOLDER = '''
UPDATED FILE ORGANIZATION:

Before (separate folder):
/output/
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.json
└── objectives/
    ├── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html
    └── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf

After (same folder - SIMPLER):
/output/
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.json
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html  ← SAME FOLDER
└── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf    ← SAME FOLDER
'''

# ============================================================================
# BENEFITS OF SAME FOLDER APPROACH
# ============================================================================

BENEFITS = '''
BENEFITS OF SAME FOLDER APPROACH:

✅ SIMPLER ORGANIZATION:
   - All lesson plan files in one place
   - Easy to find and manage
   - No subdirectory navigation needed

✅ BETTER USER EXPERIENCE:
   - Users see all files together
   - Drag-and-drop entire folder for sharing
   - Consistent with existing file patterns

✅ EASIER BACKUP:
   - Single folder contains complete lesson plan
   - Simpler file copying and archiving
   - No missing subdirectories

✅ CONSISTENT NAMING:
   - Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
   - Wilson_Weekly_W47_11-17-11-21_20251116_213107.json
   - Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html
   - Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf

✅ FRONTEND SIMPLIFICATION:
   - Same download logic for all files
   - No special handling for subdirectories
   - Consistent file path patterns
'''

# ============================================================================
# FRONTEND UPDATE (SAME FOLDER)
# ============================================================================

FRONTEND_UPDATE_SAME_FOLDER = '''
// FRONTEND CODE - No changes needed!
// The existing download logic works automatically since files are in same folder

// Existing download function works for all files:
const downloadFile = async (filePath: string) => {
    try {
        const response = await api.get(`/api/download?file=${encodeURIComponent(filePath)}`);
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', Path.basename(filePath));
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        toast.error('Download failed');
    }
};

// Download buttons remain the same:
{result.objectives_html && (
    <button onClick={() => downloadFile(result.objectives_html)}>
        Download Objectives (HTML)
    </button>
)}
{result.objectives_pdf && (
    <button onClick={() => downloadFile(result.objectives_pdf)}>
        Download Objectives (PDF)
    </button>
)}
'''

def print_same_folder_guide():
    """Print the updated integration guide for same folder approach."""
    print("=" * 80)
    print("SAVE OBJECTIVES IN SAME FOLDER AS DOCX - UPDATED GUIDE")
    print("=" * 80)
    print()
    
    print("✅ YES! Objectives can be saved in the same folder as DOCX files.")
    print("This is actually simpler and better for user experience.")
    print()
    
    print(FILE_STRUCTURE_SAME_FOLDER)
    print(BENEFITS)
    print()
    
    print("CODE CHANGE NEEDED:")
    print("-" * 50)
    print("Just replace the _generate_objectives_files method in BatchProcessor with:")
    print()
    print(OBJECTIVES_METHOD_SAME_FOLDER)
    print()
    
    print("FRONTEND:")
    print("-" * 50)
    print("No changes needed! Existing download logic works automatically.")
    print()
    
    print(FRONTEND_UPDATE_SAME_FOLDER)
    print()
    
    print("KEY CHANGE:")
    print("-" * 50)
    print("OLD: objectives_dir = docx_file.parent / 'objectives'")
    print("NEW: output_dir = docx_file.parent  # Same folder as DOCX")
    print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ All files in same folder - simpler organization")
    print("✅ No frontend changes needed - existing logic works")
    print("✅ Better user experience - easier file management")
    print("✅ Consistent naming pattern across all files")
    print("✅ Easier backup and sharing of complete lesson plans")
    print()
    print("The change is just ONE LINE in the method:")
    print("  output_dir = docx_file.parent  # Instead of creating subdirectory")



if __name__ == "__main__":
    print_same_folder_guide()

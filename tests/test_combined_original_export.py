import asyncio
import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

# Mock requirements before importing BatchProcessor
with patch('docx.Document'), patch('docxcompose.composer.Composer'):
    from tools.batch_processor import BatchProcessor
    from backend.llm_service import LLMService

async def test_combined_original_export():
    print("Starting Combined Original DOCX Export Test...")
    
    # Mock dependencies
    llm_service = MagicMock(spec=LLMService)
    with patch('tools.batch_processor.get_db'), patch('tools.batch_processor.get_tracker'):
        processor = BatchProcessor(llm_service)
    
    processor.db = MagicMock()
    processor._user_base_path = "test_base"
    
    # Mock some original plans in DB
    mock_plan1 = MagicMock()
    mock_plan1.slot_number = 1
    mock_plan1.subject = "Math"
    mock_plan1.source_file_name = "math_file.docx"
    mock_plan1.extracted_at = datetime.now()
    mock_plan1.has_no_school = False
    mock_plan1.content_json = {
        "Monday": {"Objective": "Learn fractions", "Activity": "Do math"},
        "Tuesday": {"Objective": "More fractions", "Activity": "Do more math"}
    }
    
    mock_plan2 = MagicMock()
    mock_plan2.slot_number = 2
    mock_plan2.subject = "Science"
    mock_plan2.source_file_name = "sci_file.docx"
    mock_plan2.extracted_at = datetime.now()
    mock_plan2.has_no_school = True
    mock_plan2.content_json = {
        "Monday": {"Observation": "No school today"},
    }
    
    processor.db.get_original_lesson_plans_for_week = MagicMock(return_value=[mock_plan1, mock_plan2])
    
    # Mock file manager (patch where orchestrator imports it so thread sees the mock)
    with patch('tools.batch_processor_pkg.orchestrator.get_file_manager') as mock_fm_factory:
        mock_fm = MagicMock()
        mock_fm.get_week_folder.return_value = Path("test_output")
        mock_fm_factory.return_value = mock_fm
        
        # Patch diagnostic logger so it does not try to JSON-serialize MagicMock (renderer path).
        mock_diag = MagicMock()
        # Create a minimal valid docx so that after "render" the code can re-open it with Document(temp_path).
        from docx import Document as DocxDocument
        _minimal_doc = DocxDocument()
        _minimal_doc.add_paragraph("x")
        _minimal_docx_path = Path(tempfile.gettempdir()) / "test_combined_orig_minimal.docx"
        _minimal_doc.save(str(_minimal_docx_path))
        try:
            def fake_render(self, _json_data, output_path, *args, **kwargs):
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(_minimal_docx_path, output_path)
                return True
            with patch('tools.diagnostic_logger.get_diagnostic_logger', return_value=mock_diag), \
                 patch('tools.docx_renderer.DOCXRenderer.render', fake_render):
                print("\n--- Generating Combined Original DOCX ---")
                output_path = await processor._generate_combined_original_docx(
                    "test_user", "10/06-10/10", "plan_123"
                )
                print(f"Output path: {output_path}")
                assert output_path is not None
                assert "combined_originals" in output_path
                print("\nSUCCESS: Combined Original DOCX generation verified!")
        finally:
            if _minimal_docx_path.exists():
                _minimal_docx_path.unlink()

if __name__ == "__main__":
    asyncio.run(test_combined_original_export())

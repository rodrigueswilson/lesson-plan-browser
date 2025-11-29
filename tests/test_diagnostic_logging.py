"""
Test diagnostic logging system.

Verifies that diagnostic logger correctly records hyperlink flow
and metadata at each stage.
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from tools.diagnostic_logger import DiagnosticLogger, get_diagnostic_logger, finalize_diagnostics


class TestDiagnosticLogger:
    """Test diagnostic logger functionality."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def logger(self, temp_output_dir):
        """Create diagnostic logger instance."""
        return DiagnosticLogger(output_dir=temp_output_dir)
    
    def test_logger_creates_session_directory(self, logger):
        """Test that logger creates timestamped session directory."""
        assert logger.session_dir.exists()
        assert logger.session_dir.is_dir()
        assert "session_" in logger.session_dir.name
    
    def test_log_hyperlinks_extracted(self, logger):
        """Test logging hyperlinks extracted from parser."""
        hyperlinks = [
            {"text": "Link 1", "url": "http://test1.com"},
            {"text": "Link 2", "url": "http://test2.com", "_source_slot": 1}
        ]
        
        logger.log_hyperlinks_extracted(
            slot_number=1,
            subject="ELA",
            hyperlinks=hyperlinks,
            source_file="test.docx"
        )
        
        # Check file was created
        stage_file = logger.session_dir / "01_parser_slot1.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['stage'] == "01_parser_slot1"
        assert data['data']['slot_number'] == 1
        assert data['data']['subject'] == "ELA"
        assert data['data']['hyperlink_count'] == 2
        assert len(data['data']['hyperlinks']) == 2
        assert data['data']['hyperlinks'][0]['has_source_slot'] == False
        assert data['data']['hyperlinks'][1]['has_source_slot'] == True
    
    def test_log_lesson_json_created(self, logger):
        """Test logging lesson JSON after creation."""
        lesson_json = {
            "metadata": {
                "slot_number": 1,
                "subject": "ELA"
            },
            "_hyperlinks": [
                {"text": "Link 1", "url": "http://test1.com", "_source_slot": 1, "_source_subject": "ELA"},
                {"text": "Link 2", "url": "http://test2.com"}  # Missing metadata
            ]
        }
        
        logger.log_lesson_json_created(
            slot_number=1,
            subject="ELA",
            lesson_json=lesson_json
        )
        
        # Check file
        stage_file = logger.session_dir / "02_lesson_json_slot1.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['metadata_slot_number'] == 1
        assert data['data']['metadata_subject'] == "ELA"
        assert data['data']['hyperlink_count'] == 2
        assert data['data']['hyperlinks_with_slot_metadata'] == 1
        assert data['data']['hyperlinks_with_subject_metadata'] == 1
    
    def test_log_before_render(self, logger):
        """Test logging before rendering."""
        lesson_json = {
            "metadata": {
                "slot_number": 1,
                "subject": "ELA"
            },
            "_hyperlinks": [
                {"text": "ELA Link", "_source_slot": 1, "_source_subject": "ELA"},
                {"text": "Math Link", "_source_slot": 5, "_source_subject": "Math"}
            ]
        }
        
        logger.log_before_render(
            slot_number=1,
            subject="ELA",
            lesson_json=lesson_json,
            render_type="single_slot"
        )
        
        # Check file
        stage_file = logger.session_dir / "03_before_render_slot1.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['render_type'] == "single_slot"
        assert data['data']['metadata_slot_number'] == 1
        assert data['data']['all_hyperlinks_have_slot'] == True
        assert data['data']['all_hyperlinks_have_subject'] == True
        
        # Check slot distribution
        distribution = data['data']['hyperlink_slot_distribution']
        assert distribution['1'] == 1
        assert distribution['5'] == 1
    
    def test_log_renderer_extracted_metadata(self, logger):
        """Test logging renderer metadata extraction."""
        logger.log_renderer_extracted_metadata(
            slot_number=1,
            subject="ELA",
            hyperlink_count=10,
            teacher="Test Teacher"
        )
        
        # Check file
        stage_file = logger.session_dir / "04_renderer_metadata_extracted.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['slot_number'] == 1
        assert data['data']['slot_number_is_none'] == False
        assert data['data']['filtering_will_activate'] == True
    
    def test_log_renderer_metadata_none(self, logger):
        """Test logging when renderer extracts None metadata."""
        logger.log_renderer_extracted_metadata(
            slot_number=None,
            subject=None,
            hyperlink_count=10,
            teacher="Test Teacher"
        )
        
        # Check file
        stage_file = logger.session_dir / "04_renderer_metadata_extracted.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['slot_number'] is None
        assert data['data']['slot_number_is_none'] == True
        assert data['data']['filtering_will_activate'] == False
    
    def test_log_filtering_context(self, logger):
        """Test logging filtering context."""
        logger.log_filtering_context(
            current_slot_number=1,
            current_subject="ELA",
            pending_count=50,
            cell="monday_unit_lesson"
        )
        
        # Check file
        stage_file = logger.session_dir / "05_filtering_context.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['current_slot_number'] == 1
        assert data['data']['current_slot_number_is_none'] == False
        assert data['data']['filtering_active'] == True
    
    def test_log_hyperlink_filtered(self, logger):
        """Test logging filtered hyperlink."""
        logger.log_hyperlink_filtered(
            hyperlink_text="LESSON 10: SOLVE AREA PROBLEMS",
            link_slot=5,
            current_slot=1,
            reason="slot_mismatch"
        )
        
        # Check file
        stage_file = logger.session_dir / "06_hyperlink_filtered.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['link_slot'] == 5
        assert data['data']['current_slot'] == 1
        assert data['data']['reason'] == "slot_mismatch"
    
    def test_log_hyperlink_placed(self, logger):
        """Test logging placed hyperlink."""
        logger.log_hyperlink_placed(
            hyperlink_text="Unit 2 Lesson 7",
            slot=1,
            subject="ELA",
            cell="monday_unit_lesson",
            confidence=0.95
        )
        
        # Check file
        stage_file = logger.session_dir / "07_hyperlink_placed.json"
        assert stage_file.exists()
        
        # Check content
        with open(stage_file, 'r') as f:
            data = json.load(f)
        
        assert data['data']['slot'] == 1
        assert data['data']['subject'] == "ELA"
        assert data['data']['confidence'] == 0.95
    
    def test_finalize_creates_summary(self, logger):
        """Test that finalize creates session log and summary."""
        # Log some stages
        logger.log_stage("test_stage_1", {"data": "test1"})
        logger.log_stage("test_stage_2", {"data": "test2"})
        
        # Finalize
        logger.finalize()
        
        # Check session log
        session_file = logger.session_dir / "session_log.json"
        assert session_file.exists()
        
        with open(session_file, 'r') as f:
            log = json.load(f)
        
        assert len(log) == 2
        assert log[0]['stage'] == "test_stage_1"
        assert log[1]['stage'] == "test_stage_2"
        
        # Check summary
        summary_file = logger.session_dir / "summary.json"
        assert summary_file.exists()
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        assert summary['total_stages'] == 2
        assert "test_stage_1" in summary['stages']
        assert "test_stage_2" in summary['stages']
    
    def test_count_by_slot(self, logger):
        """Test counting hyperlinks by slot."""
        hyperlinks = [
            {"_source_slot": 1},
            {"_source_slot": 1},
            {"_source_slot": 5},
            {"url": "test"}  # No metadata
        ]
        
        counts = logger._count_by_slot(hyperlinks)
        
        assert counts['1'] == 2
        assert counts['5'] == 1
        assert counts['no_metadata'] == 1


class TestDiagnosticLoggerIntegration:
    """Test diagnostic logger integration scenarios."""
    
    def test_complete_flow_logging(self, tmp_path):
        """Test logging complete hyperlink flow."""
        logger = DiagnosticLogger(output_dir=str(tmp_path))
        
        # Stage 1: Parser extraction
        logger.log_hyperlinks_extracted(
            slot_number=1,
            subject="ELA",
            hyperlinks=[{"text": "Link 1", "url": "http://test.com"}],
            source_file="test.docx"
        )
        
        # Stage 2: Lesson JSON created
        lesson_json = {
            "metadata": {"slot_number": 1, "subject": "ELA"},
            "_hyperlinks": [{"text": "Link 1", "url": "http://test.com", "_source_slot": 1, "_source_subject": "ELA"}]
        }
        logger.log_lesson_json_created(1, "ELA", lesson_json)
        
        # Stage 3: Before render
        logger.log_before_render(1, "ELA", lesson_json, "single_slot")
        
        # Stage 4: Renderer metadata
        logger.log_renderer_extracted_metadata(1, "ELA", 1, "Teacher")
        
        # Stage 5: Filtering context
        logger.log_filtering_context(1, "ELA", 1, "monday_unit_lesson")
        
        # Stage 6: Hyperlink placed
        logger.log_hyperlink_placed("Link 1", 1, "ELA", "monday_unit_lesson", 0.95)
        
        # Finalize
        logger.finalize()
        
        # Verify all files exist
        assert (logger.session_dir / "01_parser_slot1.json").exists()
        assert (logger.session_dir / "02_lesson_json_slot1.json").exists()
        assert (logger.session_dir / "03_before_render_slot1.json").exists()
        assert (logger.session_dir / "04_renderer_metadata_extracted.json").exists()
        assert (logger.session_dir / "05_filtering_context.json").exists()
        assert (logger.session_dir / "07_hyperlink_placed.json").exists()
        assert (logger.session_dir / "session_log.json").exists()
        assert (logger.session_dir / "summary.json").exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

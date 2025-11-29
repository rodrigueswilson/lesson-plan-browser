
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from backend.performance_tracker import PerformanceTracker
from tools.batch_processor import BatchProcessor
from tools.docx_renderer import DOCXRenderer

class TestPhase1(unittest.TestCase):
    def test_performance_tracker_retention(self):
        """Verify PerformanceTracker accepts retention_days and calls cleanup."""
        # Mock database
        mock_db = MagicMock()
        
        with patch('backend.performance_tracker.get_db', return_value=mock_db):
            # Initialize tracker with retention_days=7
            tracker = PerformanceTracker(enabled=True, retention_days=7)
            
            # Verify retention_days is stored
            self.assertEqual(tracker.retention_days, 7)
            
            # Set return value for delete_old_metrics to avoid TypeError in comparison
            mock_db.delete_old_metrics.return_value = 5
            
            # Verify cleanup_old_metrics called db.delete_old_metrics
            mock_db.delete_old_metrics.assert_called_with(7)
            print("PerformanceTracker retention test passed!")

    def test_performance_tracker_sampling(self):
        """Verify PerformanceTracker respects sampling_rate."""
        mock_db = MagicMock()
        
        with patch('backend.performance_tracker.get_db', return_value=mock_db):
            # Initialize with 0.0 sampling rate (should skip everything except critical)
            tracker = PerformanceTracker(enabled=True, sampling_rate=0.0)
            
            # Non-critical operation
            op_id = tracker.start_operation("plan1", "process_slot")
            self.assertEqual(op_id, "", "Should skip non-critical op with 0.0 sampling")
            
            # Critical operation
            op_id = tracker.start_operation("plan1", "batch_process")
            self.assertNotEqual(op_id, "", "Should track critical op even with 0.0 sampling")
            print("PerformanceTracker sampling test passed!")

    @patch('tools.batch_processor.DOCXParser')
    @patch('tools.batch_processor.get_db')
    @patch('tools.batch_processor.get_tracker')
    def test_batch_processor_no_school(self, mock_tracker, mock_get_db, MockParser):
        """Verify BatchProcessor handles No School days correctly."""
        # Mock dependencies
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock parser to return True for is_no_school_day
        mock_parser_instance = MockParser.return_value
        mock_parser_instance.is_no_school_day.return_value = True
        
        # Initialize processor
        processor = BatchProcessor(llm_service=MagicMock())
        processor._user_first_name = "Test"
        processor._user_last_name = "User"
        processor._user_name = "Test User"
        
        # Run _process_slot
        import asyncio
        slot_data = {
            "slot_number": 1,
            "subject": "Math",
            "primary_teacher_name": "Teacher"
        }
        
        # We need to mock _resolve_primary_file to return a dummy path
        processor._resolve_primary_file = MagicMock(return_value="dummy.docx")
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(processor._process_slot(
            slot=slot_data,
            week_of="11/24-11/28",
            provider="openai"
        ))
        
        # Verify result structure
        self.assertEqual(result['days']['monday']['unit_lesson'], "No School")
        self.assertEqual(result['days']['friday']['unit_lesson'], "No School")
        print("BatchProcessor No School test passed!")

if __name__ == '__main__':
    unittest.main()

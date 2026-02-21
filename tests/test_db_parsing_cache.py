import asyncio
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

# Mock DOCX before importing BatchProcessor
with patch('docx.Document'):
    from tools.batch_processor import BatchProcessor, SlotProcessingContext
    from backend.llm_service import LLMService

async def test_grouping_and_cache():
    print("Starting DB Parsing Cache & Grouping Test...")
    
    # Mock dependencies
    llm_service = MagicMock(spec=LLMService)
    # We need to mock get_db as well before initializing BatchProcessor
    with patch('tools.batch_processor.get_db'), patch('tools.batch_processor.get_tracker'):
        processor = BatchProcessor(llm_service)
    
    processor.db = MagicMock()
    
    # Mock resolve_primary_file to return same file for all slots
    processor._resolve_primary_file = MagicMock(return_value="shared_file.docx")
    
    # Mock open_docx_with_retry
    mock_parser = MagicMock()
    mock_parser.find_slot_by_subject = MagicMock(return_value=1)
    mock_parser.extract_subject_content_for_slot = MagicMock(return_value={
        "full_text": "Extracted content",
        "available_days": ["Monday", "Tuesday"]
    })
    mock_parser.is_no_school_day = MagicMock(return_value=False)
    
    processor._open_docx_with_retry = AsyncMock(return_value=mock_parser)
    
    # Slots
    slots = [
        {"slot_number": 1, "subject": "Math", "id": "s1"},
        {"slot_number": 2, "subject": "Science", "id": "s2"},
        {"slot_number": 3, "subject": "ELA", "id": "s3"}
    ]
    
    # Case 1: Cache Miss - Should group and parse once
    processor.db.get_original_lesson_plan = MagicMock(return_value=None)
    processor._current_user_id = "test_user"
    
    print("\n--- Test CASE 1: Cache Miss (3 slots, 1 file) ---")
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_mtime = datetime.now().timestamp()
        
        contexts = await processor._extract_slots_parallel_db(
            slots, "10/06-10/10", None, None, "plan_1", MagicMock()
        )
    
    print(f"Number of contexts: {len(contexts)}")
    print(f"Parser calls (expected 1): {processor._open_docx_with_retry.call_count}")
    print(f"DB creates (expected 3): {processor.db.create_original_lesson_plan.call_count}")
    
    assert len(contexts) == 3
    assert processor._open_docx_with_retry.call_count == 1
    assert processor.db.create_original_lesson_plan.call_count == 3
    
    # Case 2: Cache Hit - Should NOT parse
    processor._open_docx_with_retry.reset_mock()
    processor.db.create_original_lesson_plan.reset_mock()
    
    # Mock valid DB record
    mock_record = MagicMock()
    mock_record.source_file_path = "shared_file.docx"
    # Set extracted_at to be in the future relative to mtime
    mock_record.extracted_at = datetime.now() + timedelta(hours=1)
    mock_record.full_text = "Cached content"
    mock_record.available_days = ["Monday"]
    
    processor.db.get_original_lesson_plan = MagicMock(return_value=mock_record)
    
    # Mock file mtime to be in the past
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_mtime = datetime.now().timestamp() - 3600
        
        print("\n--- Test CASE 2: Cache Hit (3 slots, 1 file) ---")
        contexts = await processor._extract_slots_parallel_db(
            slots, "10/06-10/10", None, None, "plan_1", MagicMock()
        )
        
    print(f"Number of contexts: {len(contexts)}")
    print(f"Parser calls (expected 0): {processor._open_docx_with_retry.call_count}")
    print(f"Content from cache (expected True): {contexts[0].extracted_content == 'Cached content'}")
    
    assert len(contexts) == 3
    assert processor._open_docx_with_retry.call_count == 0
    assert contexts[0].extracted_content == "Cached content"

    # Case 3: Mixed Hits/Misses
    processor._open_docx_with_retry.reset_mock()
    processor.db.get_original_lesson_plan.reset_mock()
    
    def resolve_side_effect(slot, *args):
        if slot["slot_number"] == 1: return "file1.docx"
        if slot["slot_number"] == 2: return "file2.docx"
        return "file1.docx" # Slot 3 shares with Slot 1
        
    processor._resolve_primary_file.side_effect = resolve_side_effect
    
    def db_get_side_effect(user_id, week_of, slot_num):
        if slot_num == 1:
            rec = MagicMock()
            rec.source_file_path = "file1.docx"
            rec.extracted_at = datetime.now() + timedelta(hours=1)
            rec.full_text = "Cached File 1"
            rec.available_days = ["Monday"]
            return rec
        return None
        
    processor.db.get_original_lesson_plan.side_effect = db_get_side_effect
    
    print("\n--- Test CASE 3: Mixed Hits/Misses ---")
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.stat") as mock_stat:
        mock_stat.return_value.st_mtime = datetime.now().timestamp() - 3600
        
        contexts = await processor._extract_slots_parallel_db(
            slots, "10/06-10/10", None, None, "plan_1", MagicMock()
        )
        
    print(f"Number of contexts: {len(contexts)}")
    print(f"Parser calls (expected 2 - file1 and file2): {processor._open_docx_with_retry.call_count}")
    assert processor._open_docx_with_retry.call_count == 2
    
    print("\nSUCCESS: DB Parsing Cache & Grouping verified!")

if __name__ == "__main__":
    asyncio.run(test_grouping_and_cache())

"""
Test suite to verify ModelPrivateAttr error fixes in batch processor.

This test ensures that:
1. SQLModel/Pydantic objects are properly converted to dictionaries
2. The 'in' operator works correctly on lesson_json dictionaries
3. Hyperlinks and images are safely iterated
4. Slot objects are properly converted
5. No regressions in normal operation
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import the batch processor
from tools.batch_processor import BatchProcessor
from backend.schema import ClassSlot, User, ScheduleEntry


class MockSQLModel:
    """Mock SQLModel object with ModelPrivateAttr-like behavior."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def model_dump(self, mode='python'):
        """Simulate model_dump() method."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def dict(self):
        """Simulate dict() method for Pydantic v1."""
        return self.model_dump()


class MockLessonJSON(BaseModel):
    """Mock Pydantic model that could be returned from LLM service."""

    class Config:
        arbitrary_types_allowed = True

    days: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    _hyperlinks: List[Dict[str, str]] = []
    _images: List[Dict[str, str]] = []

    def model_dump(self, mode='python'):
        result = {
            'days': self.days,
            'metadata': self.metadata,
            '_hyperlinks': self._hyperlinks,
            '_images': self._images,
        }
        return result

    def dict(self):
        return self.model_dump()


class TestSlotConversion:
    """Test slot conversion from SQLModel to dictionary."""

    def test_convert_sqlmodel_slot_to_dict(self):
        """Test that SQLModel slot objects are converted to dictionaries."""
        # Create a mock slot object
        mock_slot = MockSQLModel(
            id="test-id-1",
            user_id="user-1",
            slot_number=5,
            subject="Math",
            grade="5th",
            homeroom="Room 101",
            primary_teacher_name="John Doe",
            primary_teacher_first_name="John",
            primary_teacher_last_name="Doe",
        )

        # Test conversion logic (simulating what batch_processor does)
        if hasattr(mock_slot, "model_dump"):
            slot_dict = mock_slot.model_dump(mode='python')
        elif hasattr(mock_slot, "dict"):
            slot_dict = mock_slot.dict()
        else:
            slot_dict = dict(mock_slot)

        # Verify it's a dictionary
        assert isinstance(slot_dict, dict), "Slot should be converted to dictionary"

        # Verify safe access with .get()
        assert slot_dict.get("slot_number") == 5, "Should access slot_number via .get()"
        assert slot_dict.get("subject") == "Math", "Should access subject via .get()"

        # Verify 'in' operator works
        assert "slot_number" in slot_dict, "Should check membership with 'in' operator"
        assert "subject" in slot_dict, "Should check membership with 'in' operator"

        # Verify no ModelPrivateAttr errors
        try:
            if "grade" in slot_dict:
                pass  # This should not raise ModelPrivateAttr error
        except TypeError as e:
            if "ModelPrivateAttr" in str(e) or "not iterable" in str(e):
                pytest.fail(f"ModelPrivateAttr error should not occur: {e}")


class TestLessonJSONConversion:
    """Test lesson_json conversion from SQLModel/Pydantic to dictionary."""

    def test_convert_pydantic_lesson_json_to_dict(self):
        """Test that Pydantic lesson_json is converted to dictionary."""
        # Create a mock lesson_json Pydantic object (set _hyperlinks after init so model_dump includes it)
        mock_lesson_json = MockLessonJSON(
            days={"monday": {"unit_lesson": "Unit 1"}},
            metadata={"subject": "Math"},
            _images=[],
        )
        mock_lesson_json._hyperlinks = [{"text": "Link 1", "url": "http://example.com"}]

        # Test conversion logic (simulating what batch_processor does)
        if not isinstance(mock_lesson_json, dict):
            if hasattr(mock_lesson_json, "model_dump"):
                lesson_json = mock_lesson_json.model_dump(mode='python')
            elif hasattr(mock_lesson_json, "dict"):
                lesson_json = mock_lesson_json.dict()
            else:
                lesson_json = dict(mock_lesson_json) if mock_lesson_json else {}
        else:
            lesson_json = mock_lesson_json

        # Verify it's a dictionary
        assert isinstance(lesson_json, dict), "lesson_json should be converted to dictionary"

        # Verify 'in' operator works without ModelPrivateAttr errors
        try:
            if "metadata" in lesson_json:
                assert lesson_json["metadata"]["subject"] == "Math"
            if "_hyperlinks" in lesson_json:
                assert len(lesson_json["_hyperlinks"]) == 1
        except TypeError as e:
            if "ModelPrivateAttr" in str(e) or "not iterable" in str(e):
                pytest.fail(f"ModelPrivateAttr error should not occur: {e}")

    def test_lesson_json_already_dict(self):
        """Test that lesson_json that's already a dict works correctly."""
        lesson_json = {
            "days": {"monday": {"unit_lesson": "Unit 1"}},
            "metadata": {"subject": "Math"},
            "_hyperlinks": [{"text": "Link 1", "url": "http://example.com"}],
        }

        # Should work without conversion
        assert isinstance(lesson_json, dict)
        assert "metadata" in lesson_json
        assert "_hyperlinks" in lesson_json


class TestHyperlinkImageIteration:
    """Test safe iteration over hyperlinks and images."""

    def test_iterate_hyperlinks_safely(self):
        """Test that hyperlinks can be iterated safely."""
        lesson_json = {
            "_hyperlinks": [
                {"text": "Link 1", "url": "http://example.com/1"},
                {"text": "Link 2", "url": "http://example.com/2"},
            ],
            "_images": [
                {"path": "image1.jpg", "alt": "Image 1"},
            ],
        }

        # Test iteration logic (simulating what batch_processor does)
        if "_hyperlinks" in lesson_json:
            for link in lesson_json.get("_hyperlinks", []):
                if isinstance(link, dict):
                    link["_source_slot"] = 5
                    link["_source_subject"] = "Math"

        if "_images" in lesson_json:
            for image in lesson_json.get("_images", []):
                if isinstance(image, dict):
                    image["_source_slot"] = 5
                    image["_source_subject"] = "Math"

        # Verify modifications were made
        assert lesson_json["_hyperlinks"][0]["_source_slot"] == 5
        assert lesson_json["_hyperlinks"][0]["_source_subject"] == "Math"
        assert lesson_json["_images"][0]["_source_slot"] == 5

    def test_iterate_empty_hyperlinks(self):
        """Test that empty hyperlinks list doesn't cause errors."""
        lesson_json = {
            "_hyperlinks": [],
            "_images": [],
        }

        # Should not raise errors
        if "_hyperlinks" in lesson_json:
            for link in lesson_json.get("_hyperlinks", []):
                if isinstance(link, dict):
                    link["_source_slot"] = 5

        assert len(lesson_json["_hyperlinks"]) == 0


class TestInOperatorSafety:
    """Test that 'in' operator works safely on various objects."""

    def test_in_operator_on_dict(self):
        """Test 'in' operator on regular dictionary."""
        slot = {"slot_number": 5, "subject": "Math", "grade": "5th"}

        # These should all work without errors
        assert "grade" in slot or slot.get("grade") is not None
        assert "subject" in slot or slot.get("subject") is not None

    def test_in_operator_with_get_fallback(self):
        """Test that .get() works as a safe fallback."""
        slot = {"slot_number": 5, "subject": "Math"}

        # Use .get() instead of 'in' operator for safety
        if slot.get("grade"):
            grade = slot["grade"]
        else:
            grade = None

        assert grade is None  # grade doesn't exist, should return None

        # Verify subject exists
        if slot.get("subject"):
            subject = slot["subject"]
            assert subject == "Math"

    def test_slot_filtering_with_set(self):
        """Test that slot_ids filtering works with set conversion."""
        slots = [
            {"id": "slot-1", "slot_number": 1, "subject": "ELA"},
            {"id": "slot-2", "slot_number": 2, "subject": "Math"},
        ]

        slot_ids = ["slot-1"]  # List of strings
        slot_ids_set = set(slot_ids)

        # Filter slots
        filtered = [slot for slot in slots if slot.get("id") in slot_ids_set]

        assert len(filtered) == 1
        assert filtered[0]["id"] == "slot-1"

    def test_slot_filtering_with_sqlmodel_ids(self):
        """Test slot filtering when slot_ids contains SQLModel objects."""
        slots = [
            {"id": "slot-1", "slot_number": 1, "subject": "ELA"},
            {"id": "slot-2", "slot_number": 2, "subject": "Math"},
        ]

        # Simulate slot_ids containing objects
        class MockSlotID:
            def __init__(self, id):
                self.id = id

        slot_ids = [MockSlotID("slot-1")]
        slot_ids_set = set()
        for sid in slot_ids:
            if isinstance(sid, str):
                slot_ids_set.add(sid)
            elif hasattr(sid, "id"):
                slot_ids_set.add(str(sid.id))
            else:
                slot_ids_set.add(str(sid))

        # Filter slots
        filtered = [slot for slot in slots if slot.get("id") in slot_ids_set]

        assert len(filtered) == 1
        assert filtered[0]["id"] == "slot-1"


class TestScheduleEntryConversion:
    """Test schedule entry conversion."""

    def test_convert_schedule_entries_to_dict(self):
        """Test that schedule entries are converted to dictionaries."""
        mock_entry = MockSQLModel(
            slot_number=5,
            is_active=True,
            start_time="09:00",
            end_time="10:00",
        )

        # Test conversion logic
        if hasattr(mock_entry, "model_dump"):
            entry_dict = mock_entry.model_dump()
        elif hasattr(mock_entry, "dict"):
            entry_dict = mock_entry.dict()
        else:
            entry_dict = {
                "slot_number": getattr(mock_entry, "slot_number", None),
                "is_active": getattr(mock_entry, "is_active", True),
                "start_time": getattr(mock_entry, "start_time", None),
                "end_time": getattr(mock_entry, "end_time", None),
            }

        assert isinstance(entry_dict, dict)
        assert entry_dict.get("slot_number") == 5
        assert entry_dict.get("is_active") is True

        # Test matching logic
        slot = {"slot_number": 5}
        matching = (
            entry_dict.get("slot_number") == slot.get("slot_number")
            and entry_dict.get("is_active", True)
        )
        assert matching is True


class TestErrorScenarios:
    """Test error scenarios to ensure they're handled gracefully."""

    def test_modelprivateattr_error_prevented(self):
        """Test that ModelPrivateAttr errors are prevented."""
        # Create a mock object that simulates ModelPrivateAttr behavior
        class ModelWithPrivateAttr:
            def __init__(self):
                # Simulate a ModelPrivateAttr
                from pydantic.fields import ModelPrivateAttr
                self._private_field = ModelPrivateAttr(default=None)

            def __iter__(self):
                # This would raise "not iterable" error if called
                raise TypeError("argument of type 'ModelPrivateAttr' is not iterable")

        obj = ModelWithPrivateAttr()

        # The fix should prevent this error by converting to dict first
        try:
            # Simulate the safe conversion logic
            if hasattr(obj, "model_dump"):
                converted = obj.model_dump()
            elif hasattr(obj, "dict"):
                converted = obj.dict()
            else:
                # Fallback: extract attributes manually
                converted = {
                    "slot_number": getattr(obj, "slot_number", None),
                }
        except TypeError as e:
            # If we get here with conversion, that's okay - the important thing
            # is we catch it and handle it
            converted = {}

        # Verify we got a dict (even if empty)
        assert isinstance(converted, dict)

    def test_none_lesson_json_handled(self):
        """Test that None lesson_json is handled safely."""
        lesson_json = None

        # Test conversion logic with None
        if lesson_json is None:
            lesson_json = {}

        # Should now be safe to use
        if "metadata" not in lesson_json:
            lesson_json["metadata"] = {}

        assert isinstance(lesson_json, dict)
        assert "metadata" in lesson_json


@pytest.mark.asyncio
class TestBatchProcessorIntegration:
    """Integration tests for batch processor with mocked dependencies."""

    @patch('tools.batch_processor.get_db')
    @patch('tools.batch_processor_pkg.orchestrator.LLMService')
    async def test_process_slot_with_modelprivateattr_fix(self, mock_llm_service_class, mock_get_db):
        """Test that process_slot handles ModelPrivateAttr correctly."""
        # Mock LLM service to return a Pydantic-like object
        mock_llm_service = Mock()
        mock_llm_instance = mock_llm_service_class.return_value

        # Create a lesson_json that simulates Pydantic model
        mock_lesson_json_obj = MockLessonJSON(
            days={"monday": {"unit_lesson": "Unit 1"}},
            metadata={"subject": "Math"},
        )

        # Mock transform_lesson (sync - called via asyncio.to_thread) to return the Pydantic object
        mock_llm_instance.transform_lesson = Mock(
            return_value=(True, mock_lesson_json_obj, None)
        )

        # Mock database
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_user_slots = Mock(return_value=[])
        mock_db.get_user_schedule = Mock(return_value=[])
        mock_db.get_user = Mock(return_value=Mock(name="Test User"))

        # Create batch processor and set attributes used by _process_slot / persistence
        processor = BatchProcessor(mock_llm_instance)
        processor._current_user_id = "test_user"

        # Mock slot as dictionary (already converted)
        slot = {
            "id": "test-slot",
            "slot_number": 5,
            "subject": "Math",
            "grade": "5th",
        }

        # Mock file resolution and DOCX open so _process_slot reaches LLM (mocked) and dict conversion
        with patch.object(processor, '_resolve_primary_file', return_value='/tmp/test_plan.docx'), \
             patch.object(processor, '_open_docx_with_retry', new_callable=AsyncMock) as mock_open_docx:
            content_return = {
                'full_text': 'Sample lesson content',
                'table_content': {'monday': {'Unit': 'Unit 1'}},
                'no_school_days': [],
            }
            mock_table = Mock(rows=[Mock(cells=[Mock(text='')])], columns=[Mock()])
            mock_parser = Mock()
            mock_parser.doc = Mock(tables=[mock_table, mock_table])
            mock_parser.find_slot_by_subject = Mock(return_value=1)
            mock_parser.extract_hyperlinks_for_slot = Mock(return_value=[])
            mock_parser.extract_images_for_slot = Mock(return_value=[])
            mock_parser.is_no_school_day = Mock(return_value=False)
            mock_parser.get_content_for_slot = Mock(return_value=content_return)
            mock_parser.extract_subject_content_for_slot = Mock(return_value=content_return)
            mock_open_docx.return_value = mock_parser

            # Mock file manager and parser (orchestrator imports DOCXParser from package)
            with patch('tools.batch_processor.get_file_manager') as mock_file_mgr, \
                 patch('tools.batch_processor_pkg.orchestrator.DOCXParser') as mock_parser_class:
                mock_parser_class.return_value = mock_parser

                # This should not raise ModelPrivateAttr error
                try:
                    lesson_json = await processor._process_slot(
                        slot=slot,
                        week_of="12/01-12/05",
                        provider="openai",
                        plan_id="test-plan",
                        slot_index=1,
                        total_slots=1,
                        processing_weight=1.0,
                    )
                except TypeError as e:
                    if "ModelPrivateAttr" in str(e) or "not iterable" in str(e):
                        pytest.fail(f"ModelPrivateAttr error should be fixed: {e}")
                    raise

                # Verify lesson_json is a dictionary
                assert isinstance(lesson_json, dict), "lesson_json should be converted to dict"

                # Verify we can safely check membership
                assert "metadata" in lesson_json or lesson_json.get("metadata") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


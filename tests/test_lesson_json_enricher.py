"""
Unit tests for lesson_json_enricher utility functions.
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from backend.utils.lesson_json_enricher import (
    enrich_lesson_json_from_steps,
    _batch_enrich_slots_from_steps,
    _extract_data_from_steps,
)


class MockStep:
    """Mock lesson step for testing."""
    def __init__(self, step_name: str, vocabulary_cognates: List[Dict] = None, sentence_frames: List[Dict] = None):
        self.step_name = step_name
        self.vocabulary_cognates = vocabulary_cognates or []
        self.sentence_frames = sentence_frames or []


class MockDatabase:
    """Mock database interface for testing."""
    def __init__(self):
        self.steps_by_key: Dict[tuple, List[MockStep]] = {}
    
    def get_lesson_steps(self, plan_id: str, day_of_week: str = None, slot_number: int = None):
        key = (day_of_week, slot_number)
        return self.steps_by_key.get(key, [])
    
    def set_steps(self, day: str, slot: int, steps: List[MockStep]):
        self.steps_by_key[(day, slot)] = steps


@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    return MockDatabase()


@pytest.fixture
def sample_lesson_json():
    """Create a sample lesson JSON structure."""
    return {
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "unit_lesson": "Unit 1 Lesson 1",
                        # Missing vocabulary_cognates and sentence_frames
                    },
                    {
                        "slot_number": 2,
                        "unit_lesson": "Unit 1 Lesson 2",
                        "vocabulary_cognates": [
                            {"english": "test", "portuguese": "teste"}
                        ],
                        # Missing sentence_frames
                    },
                ]
            },
            "tuesday": {
                "slot_number": 1,
                "unit_lesson": "Unit 1 Lesson 3",
                # Single-slot structure, missing both
            }
        }
    }


def test_enrich_lesson_json_empty_json(mock_db):
    """Test that empty JSON is returned unchanged."""
    result = enrich_lesson_json_from_steps({}, "plan_123", mock_db)
    assert result == {}


def test_enrich_lesson_json_no_days(mock_db):
    """Test that JSON without days is returned unchanged."""
    result = enrich_lesson_json_from_steps({"metadata": {}}, "plan_123", mock_db)
    assert result == {"metadata": {}}


def test_enrich_lesson_json_multi_slot_structure(mock_db, sample_lesson_json):
    """Test enrichment of multi-slot structure."""
    # Set up mock steps
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "word", "portuguese": "palavra"}]
    )
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "I see", "portuguese": "Eu vejo", "proficiency_level": "levels_1_2"}]
    )
    
    # Slot 1 needs both
    mock_db.set_steps("monday", 1, [vocab_step, frames_step])
    
    # Slot 2 only needs sentence_frames
    mock_db.set_steps("monday", 2, [frames_step])
    
    result = enrich_lesson_json_from_steps(sample_lesson_json, "plan_123", mock_db)
    
    # Check slot 1 was enriched
    slot1 = result["days"]["monday"]["slots"][0]
    assert "vocabulary_cognates" in slot1
    assert slot1["vocabulary_cognates"] == [{"english": "word", "portuguese": "palavra"}]
    assert "sentence_frames" in slot1
    assert len(slot1["sentence_frames"]) == 1
    
    # Check slot 2 was enriched with sentence_frames only
    slot2 = result["days"]["monday"]["slots"][1]
    assert slot2["vocabulary_cognates"] == [{"english": "test", "portuguese": "teste"}]  # Original preserved
    assert "sentence_frames" in slot2
    assert len(slot2["sentence_frames"]) == 1


def test_enrich_lesson_json_single_slot_structure(mock_db, sample_lesson_json):
    """Test enrichment of single-slot structure."""
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "hello", "portuguese": "olá"}]
    )
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "Hello", "portuguese": "Olá", "proficiency_level": "levels_1_2"}]
    )
    
    # Ensure tuesday has slot_number set
    sample_lesson_json["days"]["tuesday"]["slot_number"] = 1
    mock_db.set_steps("tuesday", 1, [vocab_step, frames_step])
    
    result = enrich_lesson_json_from_steps(sample_lesson_json, "plan_123", mock_db)
    
    tuesday_data = result["days"]["tuesday"]
    assert "vocabulary_cognates" in tuesday_data
    assert tuesday_data["vocabulary_cognates"] == [{"english": "hello", "portuguese": "olá"}]
    assert "sentence_frames" in tuesday_data
    assert len(tuesday_data["sentence_frames"]) == 1


def test_enrich_lesson_json_with_cache(mock_db, sample_lesson_json):
    """Test that caching works correctly."""
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "cached", "portuguese": "cacheado"}]
    )
    
    mock_db.set_steps("monday", 1, [vocab_step])
    
    # First call
    result1 = enrich_lesson_json_from_steps(sample_lesson_json.copy(), "plan_123", mock_db, use_cache=True)
    
    # Second call with same data - should use cache
    result2 = enrich_lesson_json_from_steps(sample_lesson_json.copy(), "plan_123", mock_db, use_cache=True)
    
    # Both should have the same result
    assert result1["days"]["monday"]["slots"][0]["vocabulary_cognates"] == result2["days"]["monday"]["slots"][0]["vocabulary_cognates"]


def test_enrich_lesson_json_no_matching_steps(mock_db, sample_lesson_json):
    """Test that JSON is unchanged when no matching steps are found."""
    # Set up empty steps
    mock_db.set_steps("monday", 1, [])
    
    original_json = sample_lesson_json.copy()
    result = enrich_lesson_json_from_steps(sample_lesson_json, "plan_123", mock_db)
    
    # Slot 1 should still be missing vocabulary_cognates
    assert "vocabulary_cognates" not in result["days"]["monday"]["slots"][0]


def test_extract_data_from_steps():
    """Test the _extract_data_from_steps helper function."""
    slot_data = {}
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "test", "portuguese": "teste"}]
    )
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "I see", "portuguese": "Eu vejo", "proficiency_level": "levels_1_2"}]
    )
    steps = [vocab_step, frames_step]
    
    _extract_data_from_steps(slot_data, steps, "plan_123", "monday", 1, True, True)
    
    assert "vocabulary_cognates" in slot_data
    assert "sentence_frames" in slot_data
    assert len(slot_data["vocabulary_cognates"]) == 1
    assert len(slot_data["sentence_frames"]) == 1


def test_extract_data_from_steps_partial():
    """Test extraction when only one field is needed."""
    slot_data = {"vocabulary_cognates": [{"english": "existing", "portuguese": "existente"}]}
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "I see", "portuguese": "Eu vejo", "proficiency_level": "levels_1_2"}]
    )
    steps = [frames_step]
    
    _extract_data_from_steps(slot_data, steps, "plan_123", "monday", 1, False, True)
    
    # vocabulary_cognates should be unchanged
    assert slot_data["vocabulary_cognates"] == [{"english": "existing", "portuguese": "existente"}]
    # sentence_frames should be added
    assert "sentence_frames" in slot_data
    assert len(slot_data["sentence_frames"]) == 1


def test_batch_enrich_slots_from_steps(mock_db):
    """Test batch enrichment of multiple slots."""
    slots_to_enrich = [
        ("monday", 1, {}),
        ("monday", 2, {}),
        ("tuesday", 1, {}),
    ]
    
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "word", "portuguese": "palavra"}]
    )
    
    mock_db.set_steps("monday", 1, [vocab_step])
    mock_db.set_steps("monday", 2, [vocab_step])
    mock_db.set_steps("tuesday", 1, [vocab_step])
    
    _batch_enrich_slots_from_steps(slots_to_enrich, "plan_123", mock_db, use_cache=True)
    
    # All slots should be enriched
    assert "vocabulary_cognates" in slots_to_enrich[0][2]
    assert "vocabulary_cognates" in slots_to_enrich[1][2]
    assert "vocabulary_cognates" in slots_to_enrich[2][2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


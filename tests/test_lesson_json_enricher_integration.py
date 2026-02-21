"""
Integration tests for lesson_json_enricher with real database patterns.
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps


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
        self.query_count = 0
    
    def get_lesson_steps(self, plan_id: str, day_of_week: str = None, slot_number: int = None):
        self.query_count += 1
        key = (day_of_week, slot_number)
        return self.steps_by_key.get(key, [])
    
    def set_steps(self, day: str, slot: int, steps: List[MockStep]):
        self.steps_by_key[(day, slot)] = steps


def test_batch_query_optimization():
    """Test that batch enrichment reduces database queries through caching."""
    mock_db = MockDatabase()
    
    # Create a lesson JSON with multiple slots missing vocabulary
    lesson_json = {
        "days": {
            "monday": {
                "slots": [
                    {"slot_number": 1},  # Missing both
                    {"slot_number": 2},  # Missing both
                    {"slot_number": 3},  # Missing both
                ]
            },
            "tuesday": {
                "slots": [
                    {"slot_number": 1},  # Missing both
                ]
            }
        }
    }
    
    # Set up steps for each slot
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "word", "portuguese": "palavra"}]
    )
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "I see", "portuguese": "Eu vejo", "proficiency_level": "levels_1_2"}]
    )
    
    for day in ["monday", "tuesday"]:
        for slot in [1, 2, 3]:
            mock_db.set_steps(day, slot, [vocab_step, frames_step])
    
    # Enrich with caching enabled
    result = enrich_lesson_json_from_steps(lesson_json, "plan_123", mock_db, use_cache=True)
    
    # Verify all slots were enriched
    assert "vocabulary_cognates" in result["days"]["monday"]["slots"][0]
    assert "vocabulary_cognates" in result["days"]["monday"]["slots"][1]
    assert "vocabulary_cognates" in result["days"]["monday"]["slots"][2]
    assert "vocabulary_cognates" in result["days"]["tuesday"]["slots"][0]
    
    # Verify database was queried (should be 4 queries: monday slots 1,2,3 and tuesday slot 1)
    # With caching, each unique (day, slot) combination is queried once
    assert mock_db.query_count == 4


def test_enrichment_preserves_existing_data():
    """Test that existing vocabulary_cognates and sentence_frames are not overwritten."""
    mock_db = MockDatabase()
    
    lesson_json = {
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "vocabulary_cognates": [{"english": "existing", "portuguese": "existente"}],
                        # Missing sentence_frames
                    }
                ]
            }
        }
    }
    
    # Set up steps with different data
    vocab_step = MockStep(
        "Vocabulary / Cognate Awareness",
        vocabulary_cognates=[{"english": "new", "portuguese": "novo"}]
    )
    frames_step = MockStep(
        "Sentence Frames / Stems / Questions",
        sentence_frames=[{"english": "I see", "portuguese": "Eu vejo", "proficiency_level": "levels_1_2"}]
    )
    
    mock_db.set_steps("monday", 1, [vocab_step, frames_step])
    
    result = enrich_lesson_json_from_steps(lesson_json, "plan_123", mock_db)
    
    # Existing vocabulary should be preserved
    assert result["days"]["monday"]["slots"][0]["vocabulary_cognates"] == [{"english": "existing", "portuguese": "existente"}]
    # Missing sentence_frames should be added
    assert "sentence_frames" in result["days"]["monday"]["slots"][0]
    assert len(result["days"]["monday"]["slots"][0]["sentence_frames"]) == 1


def test_enrichment_with_no_steps():
    """Test that enrichment gracefully handles missing steps."""
    mock_db = MockDatabase()
    
    lesson_json = {
        "days": {
            "monday": {
                "slots": [
                    {"slot_number": 1}  # Missing both, but no steps available
                ]
            }
        }
    }
    
    # Don't set any steps
    result = enrich_lesson_json_from_steps(lesson_json, "plan_123", mock_db)
    
    # JSON should be unchanged (no errors thrown)
    assert "vocabulary_cognates" not in result["days"]["monday"]["slots"][0]
    assert "sentence_frames" not in result["days"]["monday"]["slots"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


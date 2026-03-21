"""
Test vocabulary cognates and sentence frames models and validation.

Tests the new VocabularyCognatePair, SentenceFrame, and DailyPlanData models
with proper validation for counts and distributions.
"""

import json
import pytest
from pydantic import ValidationError

from backend.models_slot import (
    DailyPlanData,
    SentenceFrame,
    VocabularyCognatePair,
)


class TestVocabularyCognatePair:
    """Test VocabularyCognatePair model."""

    def test_valid_vocabulary_pair(self):
        """Test creating a valid vocabulary pair."""
        pair = VocabularyCognatePair(
            english="law",
            portuguese="lei",
            is_cognate=False,
            relevance_note="Core concept for understanding legal systems"
        )
        assert pair.english == "law"
        assert pair.portuguese == "lei"
        assert pair.is_cognate is False
        assert pair.relevance_note is not None

    def test_vocabulary_pair_minimal(self):
        """Test creating a vocabulary pair with only required fields."""
        pair = VocabularyCognatePair(
            english="system",
            portuguese="sistema"
        )
        assert pair.english == "system"
        assert pair.portuguese == "sistema"
        assert pair.is_cognate is None
        assert pair.relevance_note is None

    def test_vocabulary_pair_short_english(self):
        """Test that english word must be at least 2 characters."""
        with pytest.raises(ValidationError) as exc_info:
            VocabularyCognatePair(english="a", portuguese="palavra")
        assert "at least 2 characters" in str(exc_info.value).lower() or "min_length" in str(exc_info.value)

    def test_vocabulary_pair_short_portuguese(self):
        """Test that portuguese word must be at least 2 characters."""
        with pytest.raises(ValidationError) as exc_info:
            VocabularyCognatePair(english="word", portuguese="a")
        assert "at least 2 characters" in str(exc_info.value).lower() or "min_length" in str(exc_info.value)


class TestSentenceFrame:
    """Test SentenceFrame model."""

    def test_valid_frame_levels_1_2(self):
        """Test creating a valid frame for Levels 1-2."""
        frame = SentenceFrame(
            proficiency_level="levels_1_2",
            english="This is ___",
            portuguese="Isto é ___",
            language_function="identify",
            frame_type="frame"
        )
        assert frame.proficiency_level == "levels_1_2"
        assert frame.frame_type == "frame"

    def test_valid_frame_levels_3_4(self):
        """Test creating a valid frame for Levels 3-4."""
        frame = SentenceFrame(
            proficiency_level="levels_3_4",
            english="First ___, then ___",
            portuguese="Primeiro ___, depois ___",
            language_function="sequence",
            frame_type="frame"
        )
        assert frame.proficiency_level == "levels_3_4"
        assert frame.frame_type == "frame"

    def test_valid_stem_levels_5_6(self):
        """Test creating a valid stem for Levels 5-6."""
        frame = SentenceFrame(
            proficiency_level="levels_5_6",
            english="Evidence suggests that ___",
            portuguese="As evidências sugerem que ___",
            language_function="argue",
            frame_type="stem"
        )
        assert frame.proficiency_level == "levels_5_6"
        assert frame.frame_type == "stem"

    def test_valid_open_question_levels_5_6(self):
        """Test creating a valid open question for Levels 5-6."""
        frame = SentenceFrame(
            proficiency_level="levels_5_6",
            english="How does ___ relate to ___?",
            portuguese="Como ___ se relaciona com ___?",
            language_function="analyze",
            frame_type="open_question"
        )
        assert frame.proficiency_level == "levels_5_6"
        assert frame.frame_type == "open_question"

    def test_invalid_frame_type_levels_1_2(self):
        """Test that Levels 1-2 cannot have stem or open_question."""
        with pytest.raises(ValidationError) as exc_info:
            SentenceFrame(
                proficiency_level="levels_1_2",
                english="This is ___",
                portuguese="Isto é ___",
                language_function="identify",
                frame_type="stem"
            )
        assert "frame_type 'frame'" in str(exc_info.value)

    def test_invalid_frame_type_levels_3_4(self):
        """Test that Levels 3-4 cannot have stem or open_question."""
        with pytest.raises(ValidationError) as exc_info:
            SentenceFrame(
                proficiency_level="levels_3_4",
                english="First ___, then ___",
                portuguese="Primeiro ___, depois ___",
                language_function="sequence",
                frame_type="open_question"
            )
        assert "frame_type 'frame'" in str(exc_info.value)

    def test_invalid_frame_type_levels_5_6(self):
        """Test that Levels 5-6 cannot have frame type."""
        with pytest.raises(ValidationError) as exc_info:
            SentenceFrame(
                proficiency_level="levels_5_6",
                english="Evidence suggests that ___",
                portuguese="As evidências sugerem que ___",
                language_function="argue",
                frame_type="frame"
            )
        assert "frame_type 'stem' or 'open_question'" in str(exc_info.value)

    def test_invalid_proficiency_level(self):
        """Test that invalid proficiency level raises error."""
        with pytest.raises(ValidationError):
            SentenceFrame(
                proficiency_level="invalid_level",
                english="This is ___",
                portuguese="Isto é ___",
                language_function="identify",
                frame_type="frame"
            )

    def test_invalid_frame_type_enum(self):
        """Test that invalid frame_type raises error."""
        with pytest.raises(ValidationError):
            SentenceFrame(
                proficiency_level="levels_1_2",
                english="This is ___",
                portuguese="Isto é ___",
                language_function="identify",
                frame_type="invalid_type"
            )


class TestDailyPlanData:
    """Test DailyPlanData model with vocabulary and sentence frames."""

    def create_valid_vocabulary_list(self):
        """Helper to create exactly 6 vocabulary pairs."""
        return [
            VocabularyCognatePair(english="law", portuguese="lei", is_cognate=False),
            VocabularyCognatePair(english="system", portuguese="sistema", is_cognate=True),
            VocabularyCognatePair(english="banking", portuguese="banco", is_cognate=False),
            VocabularyCognatePair(english="economy", portuguese="economia", is_cognate=True),
            VocabularyCognatePair(english="trade", portuguese="comércio", is_cognate=False),
            VocabularyCognatePair(english="peace", portuguese="paz", is_cognate=False),
        ]

    def create_valid_sentence_frames(self):
        """Helper to create exactly 8 sentence frames with correct distribution."""
        return [
            # Levels 1-2 (3 frames)
            SentenceFrame(
                proficiency_level="levels_1_2",
                english="This is ___",
                portuguese="Isto é ___",
                language_function="identify",
                frame_type="frame",
            ),
            SentenceFrame(
                proficiency_level="levels_1_2",
                english="I see ___",
                portuguese="Eu vejo ___",
                language_function="describe",
                frame_type="frame",
            ),
            SentenceFrame(
                proficiency_level="levels_1_2",
                english="It has ___",
                portuguese="Tem ___",
                language_function="describe",
                frame_type="frame",
            ),
            # Levels 3-4 (3 frames)
            SentenceFrame(
                proficiency_level="levels_3_4",
                english="First ___, then ___",
                portuguese="Primeiro ___, depois ___",
                language_function="sequence",
                frame_type="frame",
            ),
            SentenceFrame(
                proficiency_level="levels_3_4",
                english="This shows ___ because ___",
                portuguese="Isso mostra ___ porque ___",
                language_function="explain",
                frame_type="frame",
            ),
            SentenceFrame(
                proficiency_level="levels_3_4",
                english="I think ___ because ___",
                portuguese="Eu acho ___ porque ___",
                language_function="justify",
                frame_type="frame",
            ),
            # Levels 5-6 (1 stem + 1 open question)
            SentenceFrame(
                proficiency_level="levels_5_6",
                english="Evidence suggests that ___",
                portuguese="As evidências sugerem que ___",
                language_function="argue",
                frame_type="stem",
            ),
            SentenceFrame(
                proficiency_level="levels_5_6",
                english="How does ___ relate to ___?",
                portuguese="Como ___ se relaciona com ___?",
                language_function="analyze",
                frame_type="open_question",
            ),
        ]

    def test_valid_daily_plan_with_all_fields(self):
        """Test creating a valid DailyPlanData with vocabulary and sentence frames."""
        plan = DailyPlanData(
            unit_lesson="Unit One Lesson Seven",
            vocabulary_cognates=self.create_valid_vocabulary_list(),
            sentence_frames=self.create_valid_sentence_frames()
        )
        assert len(plan.vocabulary_cognates) == 6
        assert len(plan.sentence_frames) == 8

    def test_daily_plan_vocabulary_count_lenient(self):
        """DailyPlanData does not enforce exactly 6 vocabulary rows (DB / legacy compatibility)."""
        vocab_list = self.create_valid_vocabulary_list()
        vocab_list.pop()
        plan = DailyPlanData(vocabulary_cognates=vocab_list)
        assert len(plan.vocabulary_cognates) == 5

    def test_daily_plan_sentence_frames_count_lenient(self):
        """DailyPlanData does not enforce exactly 8 sentence frames."""
        frames = self.create_valid_sentence_frames()
        frames.pop()
        plan = DailyPlanData(sentence_frames=frames)
        assert len(plan.sentence_frames) == 7

    def test_daily_plan_sentence_frames_skewed_distribution_allowed(self):
        """Non-canonical level distribution is accepted on DailyPlanData (validation is elsewhere)."""
        frames = self.create_valid_sentence_frames()
        frames = [
            f
            for f in frames
            if not (f.proficiency_level == "levels_1_2" and f.english == "It has ___")
        ]
        frames.append(
            SentenceFrame(
                proficiency_level="levels_3_4",
                english="Another frame ___",
                portuguese="Outro quadro ___",
                language_function="describe",
                frame_type="frame",
            )
        )
        plan = DailyPlanData(sentence_frames=frames)
        assert len(plan.sentence_frames) == 8

    def test_daily_plan_sentence_frames_two_stems_levels_5_6_allowed(self):
        """Two stems at levels_5_6 (no open question) still parses for slot storage."""
        frames = self.create_valid_sentence_frames()
        frames = [
            (
                f
                if f.frame_type != "open_question"
                else SentenceFrame(
                    proficiency_level="levels_5_6",
                    english="This demonstrates ___",
                    portuguese="Isso demonstra ___",
                    language_function="argue",
                    frame_type="stem",
                )
            )
            for f in frames
        ]
        plan = DailyPlanData(sentence_frames=frames)
        stems = [f for f in plan.sentence_frames if f.proficiency_level == "levels_5_6" and f.frame_type == "stem"]
        assert len(stems) == 2

    def test_daily_plan_optional_fields(self):
        """Test that vocabulary_cognates and sentence_frames are optional."""
        plan = DailyPlanData(unit_lesson="Unit One Lesson Seven")
        assert plan.vocabulary_cognates is None
        assert plan.sentence_frames is None

    def test_daily_plan_from_dict(self):
        """Test creating DailyPlanData from dictionary (as would come from JSON)."""
        data = {
            "unit_lesson": "Unit One Lesson Seven",
            "vocabulary_cognates": [
                {"english": "law", "portuguese": "lei", "is_cognate": False},
                {"english": "system", "portuguese": "sistema", "is_cognate": True},
                {"english": "banking", "portuguese": "banco", "is_cognate": False},
                {"english": "economy", "portuguese": "economia", "is_cognate": True},
                {"english": "trade", "portuguese": "comércio", "is_cognate": False},
                {"english": "peace", "portuguese": "paz", "is_cognate": False},
            ],
            "sentence_frames": [
                {
                    "proficiency_level": "levels_1_2",
                    "english": "This is ___",
                    "portuguese": "Isto é ___",
                    "language_function": "identify",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_1_2",
                    "english": "I see ___",
                    "portuguese": "Eu vejo ___",
                    "language_function": "describe",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_1_2",
                    "english": "It has ___",
                    "portuguese": "Tem ___",
                    "language_function": "describe",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "First ___, then ___",
                    "portuguese": "Primeiro ___, depois ___",
                    "language_function": "sequence",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "This shows ___ because ___",
                    "portuguese": "Isso mostra ___ porque ___",
                    "language_function": "explain",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_3_4",
                    "english": "I think ___ because ___",
                    "portuguese": "Eu acho ___ porque ___",
                    "language_function": "justify",
                    "frame_type": "frame",
                },
                {
                    "proficiency_level": "levels_5_6",
                    "english": "Evidence suggests that ___",
                    "portuguese": "As evidências sugerem que ___",
                    "language_function": "argue",
                    "frame_type": "stem",
                },
                {
                    "proficiency_level": "levels_5_6",
                    "english": "How does ___ relate to ___?",
                    "portuguese": "Como ___ se relaciona com ___?",
                    "language_function": "analyze",
                    "frame_type": "open_question",
                },
            ]
        }

        plan = DailyPlanData(**data)
        assert len(plan.vocabulary_cognates) == 6
        assert len(plan.sentence_frames) == 8
        assert plan.unit_lesson == "Unit One Lesson Seven"


class TestSchemaValidation:
    """Test JSON schema validation (if jsonschema is available)."""

    def test_schema_file_exists(self):
        """Test that the schema file exists and is valid JSON."""
        from pathlib import Path
        schema_path = Path("schemas/lesson_output_schema.json")
        assert schema_path.exists(), "Schema file should exist"

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        assert "definitions" in schema
        assert "vocabulary_cognates" in schema["definitions"]
        assert "sentence_frames" in schema["definitions"]
        
        # Check vocabulary_cognates definition
        vocab_def = schema["definitions"]["vocabulary_cognates"]
        assert vocab_def["minItems"] == 6
        assert vocab_def["maxItems"] == 6
        
        # Check sentence_frames definition
        frames_def = schema["definitions"]["sentence_frames"]
        assert frames_def["minItems"] == 8
        assert frames_def["maxItems"] == 8
        
        # Check that sentence_frames and vocabulary_cognates are required in day formats
        single_slot = schema["definitions"]["day_plan_single_slot"]
        assert "sentence_frames" in single_slot["required"]
        assert "vocabulary_cognates" in single_slot["required"]
        slot_plan = schema["definitions"]["slot_plan"]
        assert "sentence_frames" in slot_plan["required"]
        assert "vocabulary_cognates" in slot_plan["required"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


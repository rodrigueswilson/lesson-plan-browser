"""
Tests for the log errors fix plan implementations.
Tests analytics 404 fix, Phase.details optional, vocabulary_cognates trim.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from backend.lesson_schema_models import Phase
from backend.llm_service import LLMService


class TestAnalyticsErrorsEndpoint:
    """Test /api/analytics/errors endpoint (was 404 before fix).
    Requires backend running at http://127.0.0.1:8000 - skips if unreachable."""

    @pytest.fixture(autouse=True)
    def _ensure_backend(self):
        try:
            import requests

            r = requests.get("http://127.0.0.1:8000/api/health", timeout=2)
            if r.status_code != 200:
                pytest.skip("Backend not healthy")
        except Exception:
            pytest.skip("Backend not running at http://127.0.0.1:8000")

    def test_analytics_errors_returns_200(self):
        """GET /api/analytics/errors should return 200, not 404."""
        import requests

        response = requests.get(
            "http://127.0.0.1:8000/api/analytics/errors?days=30", timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_analytics_errors_with_user_id(self):
        """GET /api/analytics/errors with user_id should return 200."""
        import requests

        response = requests.get(
            "http://127.0.0.1:8000/api/analytics/errors?days=30&user_id=29fa9ed7-3174-4999-86fd-40a542c28cff",
            timeout=5,
        )
        assert response.status_code == 200

    def test_analytics_errors_returns_dict(self):
        """Response should be valid JSON with expected structure."""
        import requests

        response = requests.get(
            "http://127.0.0.1:8000/api/analytics/errors?days=7", timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestPhaseDetailsOptional:
    """Test Phase model accepts missing details (optional with default)."""

    def test_phase_without_details_validates(self):
        """Phase with no 'details' key should validate (default empty string)."""
        phase_data = {
            "phase_name": "Closure",
            "minutes": 5,
            "bilingual_teacher_role": "Lead wrap-up and reflection",
            "primary_teacher_role": "Support with content recap",
        }
        phase = Phase.model_validate(phase_data)
        assert phase.details == ""

    def test_phase_with_details_preserves(self):
        """Phase with details should preserve value."""
        phase_data = {
            "phase_name": "Warmup",
            "minutes": 5,
            "bilingual_teacher_role": "Lead vocabulary",
            "primary_teacher_role": "Support content delivery",
            "details": "Station rotation with visual timer",
        }
        phase = Phase.model_validate(phase_data)
        assert phase.details == "Station rotation with visual timer"


class TestVocabularyCognatesTrim:
    """Test vocabulary_cognates truncation when LLM returns 7 items."""

    def test_validate_structure_truncates_seven_to_six(self):
        """_validate_structure should truncate 7 vocab items to 6 and pass."""
        service = LLMService()
        lesson_json = {
            "metadata": {
                "week_of": "02/09-02/13",
                "grade": "2",
                "subject": "ELA",
                "homeroom": "310",
                "teacher_name": "Test",
            },
            "days": {
                "monday": {
                    "unit_lesson": "Unit 1",
                    "objective": {
                        "content_objective": "Learn words",
                        "student_goal": "I will learn",
                        "wida_objective": "ELD-LA.2-3.Inform.Reading Level 2",
                    },
                    "anticipatory_set": {
                        "original_content": "Intro",
                        "bilingual_bridge": "Bridge",
                    },
                    "tailored_instruction": {
                        "original_content": "Content",
                        "co_teaching_model": {
                            "model_name": "Station Teaching",
                            "rationale": "WIDA band reasoning",
                            "wida_context": "Levels 2-5",
                            "phase_plan": [
                                {
                                    "phase_name": "Warmup",
                                    "minutes": 5,
                                    "bilingual_teacher_role": "Lead vocab",
                                    "primary_teacher_role": "Support",
                                },
                                {
                                    "phase_name": "Practice",
                                    "minutes": 40,
                                    "bilingual_teacher_role": "Practice",
                                    "primary_teacher_role": "Support",
                                },
                            ],
                            "implementation_notes": ["Note"],
                        },
                        "ell_support": [
                            {
                                "strategy_id": "cognate_awareness",
                                "strategy_name": "Cognate Awareness",
                                "implementation": "Use cognates in vocabulary activities",
                                "proficiency_levels": "Levels 2-5",
                            },
                            {
                                "strategy_id": "graphic_organizers",
                                "strategy_name": "Graphic Organizers",
                                "implementation": "Use Venn diagrams",
                                "proficiency_levels": "Levels 2-4",
                            },
                            {
                                "strategy_id": "sentence_frames",
                                "strategy_name": "Sentence Frames",
                                "implementation": "Provide frames for responses",
                                "proficiency_levels": "Levels 1-4",
                            },
                        ],
                        "special_needs_support": ["Support"],
                        "materials": ["Paper"],
                    },
                    "misconceptions": {
                        "original_content": "None",
                        "linguistic_note": {
                            "pattern_id": "default",
                            "note": "No major L1 interference expected.",
                            "prevention_tip": "Monitor for common errors.",
                        },
                    },
                    "assessment": {
                        "primary_assessment": "Exit ticket",
                        "bilingual_overlay": {
                            "instrument": "Exit ticket",
                            "wida_mapping": "Inform; ELD-LA.2-3.Inform.Writing; Levels 2-4",
                            "supports_by_level": {
                                "levels_1_2": "Word bank",
                                "levels_3_4": "Sentence starters",
                                "levels_5_6": "Open response",
                            },
                            "scoring_lens": "Credit vocabulary use",
                            "constraints_honored": "No new materials",
                        },
                    },
                    "homework": {
                        "original_content": "Read",
                        "family_connection": "Discuss at home",
                    },
                    "vocabulary_cognates": [
                        {
                            "english": f"word{i}",
                            "portuguese": f"palavra{i}",
                            "is_cognate": False,
                            "relevance_note": "x",
                        }
                        for i in range(7)
                    ],
                    "sentence_frames": [
                        {
                            "proficiency_level": "levels_1_2",
                            "english": "I see ___.",
                            "portuguese": "Eu vejo ___.",
                            "language_function": "describe",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_1_2",
                            "english": "The ___ is ___.",
                            "portuguese": "O ___ e ___.",
                            "language_function": "identify",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_1_2",
                            "english": "I think ___.",
                            "portuguese": "Eu acho ___.",
                            "language_function": "argue",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_3_4",
                            "english": "First, ___.",
                            "portuguese": "Primeiro, ___.",
                            "language_function": "sequence",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_3_4",
                            "english": "Because ___.",
                            "portuguese": "Porque ___.",
                            "language_function": "explain",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_3_4",
                            "english": "I compare ___.",
                            "portuguese": "Eu comparo ___.",
                            "language_function": "compare",
                            "frame_type": "frame",
                        },
                        {
                            "proficiency_level": "levels_5_6",
                            "english": "Evidence suggests ___.",
                            "portuguese": "As evidencias sugerem ___.",
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
                    ],
                },
            },
        }
        valid, err = service._validate_structure(lesson_json)
        assert valid, f"Validation should pass after truncation: {err}"
        assert len(lesson_json["days"]["monday"]["vocabulary_cognates"]) == 6

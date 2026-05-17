"""Tests for WIDA ELD code normalization and validation (backend.wida_eld_format)."""

import pytest

from backend.lesson_schema_models import Objective
from backend.llm.post_process import normalize_wida_objectives_in_lesson_json
from backend.models_slot import ObjectiveData
from backend.wida_eld_format import (
    normalize_eld_function_domain_slash,
    validate_and_normalize_wida_objective,
)


def _long_wida_with_eld(eld_fragment: str) -> str:
    return (
        "Students will use language to explain key concepts and participate in discussions "
        f"using supports appropriate for WIDA levels 2-4 ({eld_fragment})."
    )


class TestNormalizeEldFunctionDomainSlash:
    def test_fixes_function_domain_slash(self):
        text = "prefix (ELD-SS.6-8.Explain/Speaking/Writing) suffix"
        assert (
            normalize_eld_function_domain_slash(text)
            == "prefix (ELD-SS.6-8.Explain.Speaking/Writing) suffix"
        )

    def test_idempotent_on_valid_format(self):
        text = "prefix (ELD-SS.6-8.Explain.Speaking/Writing) suffix"
        assert normalize_eld_function_domain_slash(text) == text


class TestValidateAndNormalizeWidaObjective:
    def test_normalizes_slash_format(self):
        raw = _long_wida_with_eld("ELD-SS.6-8.Explain/Speaking/Writing")
        result = validate_and_normalize_wida_objective(raw)
        assert "ELD-SS.6-8.Explain.Speaking/Writing" in result
        assert "Explain/Speaking" not in result

    def test_valid_format_unchanged(self):
        raw = _long_wida_with_eld("ELD-SS.6-8.Explain.Speaking/Writing")
        assert validate_and_normalize_wida_objective(raw) == raw

    def test_missing_eld_raises(self):
        raw = (
            "Students will use language to explain key concepts without an ELD code "
            "using supports appropriate for WIDA levels 2-4 in class."
        )
        with pytest.raises(ValueError, match="ELD code"):
            validate_and_normalize_wida_objective(raw)

    def test_no_school_passthrough(self):
        assert validate_and_normalize_wida_objective("no school") == "no school"

    def test_double_normalize_is_idempotent(self):
        raw = _long_wida_with_eld("ELD-SS.6-8.Explain/Speaking/Writing")
        once = validate_and_normalize_wida_objective(raw)
        twice = validate_and_normalize_wida_objective(once)
        assert once == twice


class TestLessonSchemaObjective:
    def test_objective_accepts_slash_format_via_validator(self):
        wida = _long_wida_with_eld("ELD-SS.6-8.Explain/Speaking/Writing")
        obj = Objective(
            content_objective="Students will explain Roman systems of law and trade.",
            student_goal="I will explain Roman systems using evidence (speaking).",
            wida_objective=wida,
        )
        assert "ELD-SS.6-8.Explain.Speaking/Writing" in obj.wida_objective


class TestObjectiveDataDelegation:
    def test_objective_data_normalizes_slash_format(self):
        wida = _long_wida_with_eld("ELD-MA.3-5.Compare/Speaking")
        obj = ObjectiveData(
            content_objective="Students will compare fractions",
            student_goal="I will speak about fractions (speaking).",
            wida_objective=wida,
        )
        assert "ELD-MA.3-5.Compare.Speaking" in obj.wida_objective


class TestPostProcessLessonJson:
    def test_normalizes_thursday_objective_in_place(self):
        wida = _long_wida_with_eld("ELD-SS.6-8.Explain/Speaking/Writing")
        lesson_json = {
            "days": {
                "thursday": {
                    "objective": {
                        "wida_objective": wida,
                    }
                }
            }
        }
        normalize_wida_objectives_in_lesson_json(lesson_json)
        assert "Explain.Speaking/Writing" in lesson_json["days"]["thursday"]["objective"][
            "wida_objective"
        ]
        assert "Explain/Speaking" not in lesson_json["days"]["thursday"]["objective"][
            "wida_objective"
        ]

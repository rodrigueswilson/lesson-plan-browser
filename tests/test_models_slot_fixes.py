"""
Tests for ModelPrivateAttr fixes in models_slot.py
"""
import pytest
from pydantic import ValidationError
from backend.models_slot import ObjectiveData


class TestModelPrivateAttrFixes:
    """Test that ModelPrivateAttr errors are properly handled."""

    def test_allowed_domains_with_valid_student_goal(self):
        """Test that student_goal validation works with valid domains."""
        obj = ObjectiveData(
            content_objective="Students will understand the water cycle",
            student_goal="I will explain the water cycle (listening, speaking).",
            wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
        )
        assert obj.student_goal == "I will explain the water cycle (listening, speaking)."

    def test_allowed_domains_with_invalid_domain(self):
        """Test that invalid domains are rejected."""
        # First test: domain not mentioned in goal text (fails domain pattern check)
        with pytest.raises(ValidationError) as exc_info:
            ObjectiveData(
                content_objective="Students will understand the water cycle",
                student_goal="I will explain the water cycle (invalid_domain).",
                wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
            )
        # The error happens at domain pattern check first
        assert "must mention at least one WIDA language domain" in str(exc_info.value)
        
        # Second test: domain mentioned but invalid in parentheses (fails allowed domains check)
        with pytest.raises(ValidationError) as exc_info2:
            ObjectiveData(
                content_objective="Students will understand the water cycle",
                student_goal="I will explain the water cycle (listening, invalid_domain).",
                wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
            )
        # This should fail at allowed domains check
        assert "may only include listening, reading, speaking, or writing" in str(exc_info2.value)

    def test_allowed_domains_with_all_valid_domains(self):
        """Test that all four valid domains work."""
        obj = ObjectiveData(
            content_objective="Students will understand the water cycle",
            student_goal="I will explain the water cycle (listening, reading, speaking, writing).",
            wida_objective="ELD-SC.3-5.Explain.Listening/Reading/Speaking/Writing Students will explain the water cycle using all language domains.",
        )
        assert obj.student_goal == "I will explain the water cycle (listening, reading, speaking, writing)."

    def test_no_school_values_handling(self):
        """Test that no school values are handled correctly."""
        obj = ObjectiveData(
            content_objective="no school",
            student_goal="no school",
            wida_objective="no school",
        )
        assert obj.content_objective == "no school"
        assert obj.student_goal == "no school"
        assert obj.wida_objective == "no school"

    def test_wida_pattern_validation(self):
        """Test that WIDA pattern validation works."""
        obj = ObjectiveData(
            content_objective="Students will understand the water cycle",
            student_goal="I will explain the water cycle (listening, speaking).",
            wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
        )
        assert "ELD-SC.3-5.Explain" in obj.wida_objective

    def test_domain_pattern_validation(self):
        """Test that domain pattern validation works."""
        # Should pass with valid domain mention
        obj = ObjectiveData(
            content_objective="Students will understand the water cycle",
            student_goal="I will explain the water cycle (listening, speaking).",
            wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
        )
        assert "listening" in obj.student_goal.lower()

    def test_parentheses_pattern_validation(self):
        """Test that parentheses pattern validation works."""
        # Should pass with valid parentheses
        obj = ObjectiveData(
            content_objective="Students will understand the water cycle",
            student_goal="I will explain the water cycle (listening, speaking).",
            wida_objective="ELD-SC.3-5.Explain.Listening/Speaking Students will explain the water cycle using listening and speaking skills.",
        )
        assert ")." in obj.student_goal

    def test_helper_methods_exist(self):
        """Test that helper methods exist and work."""
        assert hasattr(ObjectiveData, "_get_allowed_domains")
        assert hasattr(ObjectiveData, "_get_no_school_values")
        assert hasattr(ObjectiveData, "_get_domain_pattern")
        assert hasattr(ObjectiveData, "_get_parentheses_pattern")
        assert hasattr(ObjectiveData, "_get_wida_pattern")

        # Test that they return correct types
        domains = ObjectiveData._get_allowed_domains()
        assert isinstance(domains, set)
        assert "listening" in domains
        assert "reading" in domains
        assert "speaking" in domains
        assert "writing" in domains

        no_school = ObjectiveData._get_no_school_values()
        assert isinstance(no_school, set)
        assert "no school" in no_school

        domain_pattern = ObjectiveData._get_domain_pattern()
        assert hasattr(domain_pattern, "search")  # Should be a regex pattern

        parentheses_pattern = ObjectiveData._get_parentheses_pattern()
        assert hasattr(parentheses_pattern, "search")  # Should be a regex pattern

        wida_pattern = ObjectiveData._get_wida_pattern()
        assert hasattr(wida_pattern, "search")  # Should be a regex pattern


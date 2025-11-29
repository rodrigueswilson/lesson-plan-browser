"""
Test WIDA Domain Selection Modifications

Tests the flexible domain selection feature that allows objectives to include
1-4 language domains based on lesson activities rather than always requiring all four.
"""

import pytest
from backend.llm_service import LLMService
from backend.models_slot import ObjectiveData


class TestDomainAnalysis:
    """Test the _analyze_domains_from_activities() helper method"""

    def test_think_pair_share_detects_listening_speaking(self):
        """Test that Think-Pair-Share strategy detects Listening + Speaking"""
        service = LLMService(provider="openai")
        
        ell_support = [
            {
                "strategy_id": "think_pair_share",
                "strategy_name": "Think-Pair-Share",
                "implementation": "...",
                "proficiency_levels": "Levels 2-5",
            }
        ]
        
        domains = service._analyze_domains_from_activities(ell_support=ell_support)
        
        assert domains["listening"] is True, "Think-Pair-Share should detect listening"
        assert domains["speaking"] is True, "Think-Pair-Share should detect speaking"
        assert domains["reading"] is False, "Think-Pair-Share should not detect reading"
        assert domains["writing"] is False, "Think-Pair-Share should not detect writing"

    def test_collaborative_learning_detects_listening_speaking(self):
        """Test that Collaborative Learning strategy detects Listening + Speaking"""
        service = LLMService(provider="openai")
        
        ell_support = [
            {
                "strategy_id": "collaborative_learning",
                "strategy_name": "Collaborative Learning",
                "implementation": "...",
            }
        ]
        
        domains = service._analyze_domains_from_activities(ell_support=ell_support)
        
        assert domains["listening"] is True
        assert domains["speaking"] is True
        assert domains["reading"] is False
        assert domains["writing"] is False

    def test_sentence_frames_detects_speaking_writing(self):
        """Test that Sentence Frames strategy detects Speaking + Writing"""
        service = LLMService(provider="openai")
        
        ell_support = [
            {
                "strategy_id": "sentence_frames",
                "strategy_name": "Sentence Frames",
                "implementation": "...",
            }
        ]
        
        domains = service._analyze_domains_from_activities(ell_support=ell_support)
        
        assert domains["speaking"] is True
        assert domains["writing"] is True
        assert domains["listening"] is False
        assert domains["reading"] is False

    def test_literature_circles_detects_three_domains(self):
        """Test that Literature Circles detects Reading + Speaking + Listening"""
        service = LLMService(provider="openai")
        
        ell_support = [
            {
                "strategy_id": "literature_circles",
                "strategy_name": "Literature Circles",
                "implementation": "...",
            }
        ]
        
        domains = service._analyze_domains_from_activities(ell_support=ell_support)
        
        assert domains["reading"] is True
        assert domains["speaking"] is True
        assert domains["listening"] is True
        assert domains["writing"] is False

    def test_phase_plan_keyword_detection(self):
        """Test that phase plan activities are analyzed via keywords"""
        service = LLMService(provider="openai")
        
        phase_plan = [
            {
                "phase_name": "Reading Activity",
                "bilingual_teacher_role": "Students will read the text",
                "primary_teacher_role": "Guide reading comprehension",
                "details": "Students read passages and write responses",
            }
        ]
        
        domains = service._analyze_domains_from_activities(phase_plan=phase_plan)
        
        assert domains["reading"] is True, "Should detect reading from keywords"
        assert domains["writing"] is True, "Should detect writing from keywords"
        assert domains["listening"] is False
        assert domains["speaking"] is False

    def test_content_objective_hints(self):
        """Test that content objective provides domain hints"""
        service = LLMService(provider="openai")
        
        content_objective = "Students will read informational texts and write summaries"
        
        domains = service._analyze_domains_from_activities(
            content_objective=content_objective
        )
        
        assert domains["reading"] is True, "Should detect reading from content objective"
        assert domains["writing"] is True, "Should detect writing from content objective"
        assert domains["listening"] is False
        assert domains["speaking"] is False

    def test_combined_analysis(self):
        """Test that all sources (strategies, phase_plan, content_objective) are combined"""
        service = LLMService(provider="openai")
        
        ell_support = [
            {
                "strategy_id": "think_pair_share",
                "strategy_name": "Think-Pair-Share",
                "implementation": "...",
            }
        ]
        
        phase_plan = [
            {
                "phase_name": "Writing Response",
                "bilingual_teacher_role": "Students write paragraphs",
                "primary_teacher_role": "...",
                "details": "...",
            }
        ]
        
        content_objective = "Students will read the story"
        
        domains = service._analyze_domains_from_activities(
            ell_support=ell_support,
            phase_plan=phase_plan,
            content_objective=content_objective,
        )
        
        # Should detect all domains from combined sources
        assert domains["listening"] is True, "From think_pair_share"
        assert domains["speaking"] is True, "From think_pair_share"
        assert domains["reading"] is True, "From content_objective"
        assert domains["writing"] is True, "From phase_plan"

    def test_no_activities_returns_all_false(self):
        """Test that with no activities, all domains are False"""
        service = LLMService(provider="openai")
        
        domains = service._analyze_domains_from_activities()
        
        assert domains["listening"] is False
        assert domains["reading"] is False
        assert domains["speaking"] is False
        assert domains["writing"] is False


class TestPromptIncludesDomainGuidance:
    """Test that prompts include domain selection guidance"""

    def test_structured_outputs_prompt_includes_domain_section(self):
        """Test that structured outputs prompt includes WIDA domain selection section"""
        service = LLMService(provider="openai")
        service.model = "gpt-4o"  # Supports structured outputs
        
        prompt = service._build_prompt(
            primary_content="Test content",
            grade="5",
            subject="Math",
            week_of="10/6-10/10",
            teacher_name="Ms. Smith",
            homeroom="302",
        )
        
        assert "WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION" in prompt
        assert "Select 1-4 domains based on" in prompt
        assert "objective.student_goal REQUIREMENTS" in prompt
        assert "objective.wida_objective REQUIREMENTS" in prompt
        assert "Do NOT force all four domains" in prompt

    def test_non_structured_outputs_prompt_includes_domain_section(self):
        """Test that non-structured outputs prompt includes WIDA domain selection section"""
        service = LLMService(provider="openai")
        service.model = "gpt-3.5-turbo"  # Doesn't support structured outputs
        
        prompt = service._build_prompt(
            primary_content="Test content",
            grade="5",
            subject="Math",
            week_of="10/6-10/10",
            teacher_name="Ms. Smith",
            homeroom="302",
        )
        
        assert "WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION" in prompt
        assert "Select 1-4 domains based on" in prompt
        assert "objective.student_goal REQUIREMENTS" in prompt
        assert "objective.wida_objective REQUIREMENTS" in prompt

    def test_prompt_includes_examples_for_all_domain_counts(self):
        """Test that prompt includes examples for 1, 2, 3, and 4 domains"""
        service = LLMService(provider="openai")
        
        prompt = service._build_prompt(
            primary_content="Test content",
            grade="5",
            subject="Math",
            week_of="10/6-10/10",
            teacher_name="Ms. Smith",
            homeroom="302",
        )
        
        # Check for examples
        assert "1 domain (Writing only)" in prompt
        assert "2 domains (Listening + Speaking)" in prompt
        assert "2 domains (Reading + Writing)" in prompt
        assert "3 domains (Reading + Speaking + Writing)" in prompt
        assert "4 domains (All)" in prompt


class TestSchemaExamples:
    """Test that schema examples show flexible domain selection"""

    def test_schema_example_includes_flexible_domains(self):
        """Test that schema example shows flexible domain selection"""
        service = LLMService(provider="openai")
        
        schema_example = service._build_schema_example(
            week_of="10/6-10/10",
            grade="5",
            subject="Science",
            teacher_name="Ms. Johnson",
            homeroom="302",
        )
        
        # Parse the JSON
        import json
        example_data = json.loads(schema_example)
        
        # Check Monday example has concrete domain example
        monday_objective = example_data["days"]["monday"]["objective"]
        
        assert "wida_objective" in monday_objective
        assert "student_goal" in monday_objective
        
        # Check that the example shows all 4 domains
        wida_obj = monday_objective["wida_objective"]
        assert "listening" in wida_obj.lower()
        assert "reading" in wida_obj.lower()
        assert "speaking" in wida_obj.lower()
        assert "writing" in wida_obj.lower()
        assert "ELD-" in wida_obj  # Should have ELD code
        assert "Listening/Reading/Speaking/Writing" in wida_obj
        
        # Check student goal is child-friendly
        student_goal = monday_objective["student_goal"]
        assert student_goal.startswith("I will")
        assert len(student_goal.split()) <= 20  # Should be concise


class TestValidation:
    """Test validation with different domain formats"""

    def test_validation_accepts_single_domain(self):
        """Test that validation accepts single domain ELD code"""
        wida_objective = (
            "Students will explain the water cycle through writing a paragraph "
            "describing each stage, using sentence frames and vocabulary supports "
            "appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Writing)."
        )
        
        # Should not raise validation error
        obj = ObjectiveData(
            content_objective="Students will explain the water cycle",
            student_goal="I will write about the water cycle.",
            wida_objective=wida_objective,
        )
        
        assert obj.wida_objective == wida_objective

    def test_validation_accepts_multiple_domains(self):
        """Test that validation accepts multiple domains in ELD code"""
        wida_objective = (
            "Students will compare fractions through listening to explanations "
            "and speaking with partners using sentence frames, using visual supports "
            "appropriate for WIDA levels 2-3 (ELD-MA.3-5.Compare.Listening/Speaking)."
        )
        
        obj = ObjectiveData(
            content_objective="Students will compare fractions",
            student_goal="I will listen and speak about fractions.",
            wida_objective=wida_objective,
        )
        
        assert obj.wida_objective == wida_objective

    def test_validation_accepts_all_four_domains(self):
        """Test that validation accepts all four domains in ELD code"""
        wida_objective = (
            "Students will explain historical events through listening to primary sources, "
            "reading documents, speaking in discussions, and writing summaries, using cognates "
            "and sentence frames appropriate for WIDA levels 2-4 "
            "(ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)."
        )
        
        obj = ObjectiveData(
            content_objective="Students will explain historical events",
            student_goal="I will listen, read, speak, and write about history.",
            wida_objective=wida_objective,
        )
        
        assert obj.wida_objective == wida_objective

    def test_validation_rejects_missing_eld_code(self):
        """Test that validation rejects objectives without ELD code"""
        wida_objective = (
            "Students will explain the water cycle through writing a paragraph "
            "describing each stage, using sentence frames and vocabulary supports."
        )
        
        with pytest.raises(ValueError, match="ELD code"):
            ObjectiveData(
                content_objective="Students will explain the water cycle",
                student_goal="I will write about the water cycle.",
                wida_objective=wida_objective,
            )

    def test_validation_error_message_shows_examples(self):
        """Test that validation error message shows domain notation examples"""
        wida_objective = "Students will explain something without an ELD code."
        
        with pytest.raises(ValueError) as exc_info:
            ObjectiveData(
                content_objective="Test",
                student_goal="I will test.",
                wida_objective=wida_objective,
            )
        
        error_message = str(exc_info.value)
        assert "ELD code with domain(s)" in error_message
        assert "ELD-SS.6-8.Explain.Writing" in error_message
        assert "ELD-SS.6-8.Explain.Listening/Speaking" in error_message
        assert "Listening/Reading/Speaking/Writing" in error_message


class TestStudentGoalRequirements:
    """Test that student goals meet requirements"""

    def test_student_goal_starts_with_i_will(self):
        """Test that student goals start with 'I will'"""
        valid_goals = [
            "I will write a paragraph about the water cycle.",
            "I will listen to my partner and speak to share my ideas.",
            "I will read the story and write about my favorite part.",
        ]
        
        for goal in valid_goals:
            obj = ObjectiveData(
                content_objective="Test objective",
                student_goal=goal,
                wida_objective="Students will test through writing paragraphs using supports appropriate for WIDA levels 2-4 (ELD-TS.1-2.Test.Writing).",
            )
            assert obj.student_goal == goal

    def test_student_goal_length_validation(self):
        """Test that student goals respect length limits"""
        # Valid: under 80 characters
        valid_goal = "I will listen, read, speak, and write about the water cycle."
        assert len(valid_goal) <= 80
        
        obj = ObjectiveData(
            content_objective="Students will learn about the water cycle.",
            student_goal=valid_goal,
            wida_objective="Students will test through listening, reading, speaking, and writing using supports appropriate for WIDA levels 2-4 (ELD-TS.1-2.Test.Listening/Reading/Speaking/Writing).",
        )
        assert obj.student_goal == valid_goal
        
        # Invalid: over 80 characters
        invalid_goal = "I will " + "do many things " * 10 + "about the topic."
        assert len(invalid_goal) > 80
        
        with pytest.raises(ValueError, match="80 characters"):
            ObjectiveData(
                content_objective="Students will learn about the topic.",
                student_goal=invalid_goal,
                wida_objective="Students will test through writing paragraphs using supports appropriate for WIDA levels 2-4 (ELD-TS.1-2.Test.Writing).",
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


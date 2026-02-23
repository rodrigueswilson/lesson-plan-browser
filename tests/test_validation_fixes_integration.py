"""
Integration tests for validation error fixes:
- End-to-end transformation with improved error handling
- Retry scenarios with enhanced error feedback
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.llm_service import LLMService


class TestEndToEndTransformation:
    """Test end-to-end transformation with fixes applied"""
    
    @patch('backend.llm_service.instructor')
    @patch('backend.llm_service.OpenAI')
    def test_instructor_path_no_fallback(self, mock_openai, mock_instructor):
        """Test that instructor path doesn't fall back due to enum serialization"""
        # Mock OpenAI client
        mock_client_instance = Mock()
        mock_openai.return_value = mock_client_instance
        
        # Mock instructor client
        mock_instructor_client = Mock()
        mock_instructor.from_openai.return_value = mock_instructor_client
        
        # Create mock response with enum
        from backend.lesson_schema_enums import FrameType, ProficiencyLevel
        from backend.lesson_schema_models import (
            BilingualLessonPlanOutputSchema,
            Days,
            DayPlan,
            DayPlanSingleSlot,
        )
        from backend.lesson_schema_vocabulary import SentenceFrame
        
        # Create a valid lesson plan with enum
        sentence_frame = SentenceFrame(
            proficiency_level=ProficiencyLevel.levels_1_2,
            english="Test frame",
            portuguese="Teste frame",
            language_function="identify",
            frame_type="frame"
        )
        # Schema requires exactly 8 sentence frames
        sentence_frames_list = [sentence_frame] * 8

        day_plan = DayPlanSingleSlot(
            unit_lesson="Test Lesson",
            sentence_frames=sentence_frames_list
        )
        
        days = Days(monday=DayPlan(root=day_plan))
        
        mock_schema = BilingualLessonPlanOutputSchema(
            metadata={
                "week_of": "10/6-10/10",
                "grade": "2",
                "subject": "Math",
                "homeroom": "T1",
                "teacher_name": "Test Teacher",
            },
            days=days
        )
        
        # Mock completion with usage
        mock_completion = Mock()
        mock_usage = Mock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 200
        mock_usage.total_tokens = 300
        mock_completion.usage = mock_usage
        
        # Mock the create_with_completion call
        mock_instructor_client.chat.completions.create_with_completion = Mock(
            return_value=(mock_schema, mock_completion)
        )
        
        # Create service
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = LLMService(provider="openai")
            
            # Call instructor method
            result_dict, usage = service._call_instructor_chat_completion("test prompt")
            
            # Verify no exception was raised (enum serialization worked)
            assert isinstance(result_dict, dict)
            assert usage['tokens_input'] == 100
            assert usage['tokens_output'] == 200
            
            # Verify instructor was called (not fallback to legacy)
            mock_instructor_client.chat.completions.create_with_completion.assert_called_once()
    
    @patch('backend.llm_service.instructor')
    def test_error_parsing_in_retry_flow(self, mock_instructor):
        """Test that error parsing is integrated into retry flow"""
        service = LLMService(provider="openai")
        
        # Simulate a validation error
        validation_error = """
        days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
          Input should be 'subject_pronoun_omission' or 'default'
          [type=enum, input_value='invalid_pattern', input_type=str]
        days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping
          String should match pattern '.*ELD.*Level'
          [type=string_pattern_mismatch, input_value='Invalid', input_type=str]
        """
        
        # Parse errors
        parsed = service._parse_validation_errors(validation_error)
        
        # Verify parsing worked
        assert parsed['has_errors'] is True
        assert len(parsed['enum_errors']) > 0
        assert len(parsed['pattern_errors']) > 0
        
        # Verify retry prompt includes parsed error guidance
        retry_prompt = service._build_retry_prompt(
            original_prompt="Original",
            validation_error=validation_error,
            retry_count=1
        )
        
        assert "ENUM VALUE ERRORS" in retry_prompt
        assert "PATTERN MISMATCH ERRORS" in retry_prompt
        assert "subject_pronoun_omission" in retry_prompt


class TestRetryScenarios:
    """Test retry scenarios with enhanced error feedback"""
    
    def test_structure_confusion_retry(self):
        """Test retry with structure confusion error"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.slots
          Extra inputs are not permitted [type=extra_forbidden]
        days.monday.DayPlanMultiSlot.unit_lesson
          Extra inputs are not permitted [type=extra_forbidden]
        """
        
        retry_prompt = service._build_retry_prompt(
            original_prompt="Original prompt",
            validation_error=error_msg,
            retry_count=2
        )
        
        # Verify structure guidance is included
        assert "STRUCTURE CONFUSION DETECTED" in retry_prompt
        assert "DayPlanSingleSlot" in retry_prompt
        assert "slots" in retry_prompt or "DO NOT include this field" in retry_prompt
        assert "RETRY ATTEMPT 2" in retry_prompt
    
    def test_enum_error_retry(self):
        """Test retry with enum error"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
          Input should be 'subject_pronoun_omission', 'adjective_placement', 'past_tense_ed_dropping', 'preposition_depend_on', 'false_cognate_actual', 'false_cognate_library' or 'default'
          [type=enum, input_value='direction_words_confusion', input_type=str]
        """
        
        retry_prompt = service._build_retry_prompt(
            original_prompt="Original prompt",
            validation_error=error_msg,
            retry_count=1
        )
        
        # Verify enum guidance is included
        assert "ENUM VALUE ERRORS" in retry_prompt
        assert "direction_words_confusion" in retry_prompt  # Invalid value shown
        assert "subject_pronoun_omission" in retry_prompt  # Allowed value shown
        assert "Allowed values" in retry_prompt
    
    def test_pattern_error_retry(self):
        """Test retry with pattern error"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping
          String should match pattern '.*(Explain|Narrate|Inform|Argue).*ELD.*Level'
          [type=string_pattern_mismatch, input_value='Inform; ELD-MA.2-3.Infor...ey Language Use: Inform', input_type=str]
        """
        
        retry_prompt = service._build_retry_prompt(
            original_prompt="Original prompt",
            validation_error=error_msg,
            retry_count=1
        )
        
        # Verify pattern guidance is included
        assert "PATTERN MISMATCH ERRORS" in retry_prompt
        assert "ELD.*Level" in retry_prompt
        assert "Inform; ELD-MA.2-3" in retry_prompt  # Invalid value shown


class TestSchemaEnforcement:
    """Test that schema changes are properly enforced"""
    
    def test_single_slot_structure_only(self):
        """Test that only single-slot structure is accepted"""
        from backend.lesson_schema_models import DayPlan, DayPlanSingleSlot
        
        # Valid single-slot structure
        single_slot = DayPlanSingleSlot(unit_lesson="Test")
        day_plan = DayPlan(root=single_slot)
        
        # Should serialize correctly
        dumped = day_plan.model_dump()
        assert 'unit_lesson' in dumped
        assert dumped['unit_lesson'] == "Test"
        
        # Should not have slots field
        assert 'slots' not in dumped
    
    def test_prompt_includes_enum_documentation(self):
        """Test that prompt includes enum value documentation"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = LLMService(provider="openai")
            
            prompt = service._build_prompt(
                primary_content="Test content",
                grade="2",
                subject="Math",
                week_of="10/6-10/10",
                teacher_name="Test Teacher",
                homeroom="101"
            )
            
            # Verify enum documentation is included
            assert "pattern_id ENUM VALUES" in prompt or "pattern_id" in prompt
            assert "subject_pronoun_omission" in prompt
            assert "proficiency_level ENUM VALUES" in prompt or "levels_1_2" in prompt
            assert "wida_mapping PATTERN REQUIREMENT" in prompt or "ELD.*Level" in prompt

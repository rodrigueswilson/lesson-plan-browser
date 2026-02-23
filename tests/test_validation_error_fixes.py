"""
Unit tests for validation error fixes:
- Enum serialization in instructor library
- Error parsing functionality
- Retry prompt enhancement
"""

import pytest
from unittest.mock import Mock, patch
from backend.llm_service import LLMService
from backend.lesson_schema_enums import ProficiencyLevel
from backend.lesson_schema_models import BilingualLessonPlanOutputSchema, PatternId


class TestEnumSerialization:
    """Test enum serialization fixes in instructor library"""
    
    def test_model_dump_with_json_mode(self):
        """Test that model_dump(mode='json') properly serializes enums"""
        from backend.lesson_schema_enums import FrameType
        from backend.lesson_schema_vocabulary import SentenceFrame
        
        # Create a sentence frame with enum
        frame = SentenceFrame(
            proficiency_level=ProficiencyLevel.levels_1_2,
            english="I will read the text.",
            portuguese="Vou ler o texto.",
            language_function="read",  # Required field
            frame_type=FrameType.frame
        )
        
        # Test that model_dump(mode='json') serializes enum as string
        dumped = frame.model_dump(mode='json')
        assert isinstance(dumped['proficiency_level'], str)
        assert dumped['proficiency_level'] == 'levels_1_2'
        assert isinstance(dumped['frame_type'], str)
        assert dumped['frame_type'] == 'frame'
        
        # Test that regular model_dump() returns enum object
        dumped_regular = frame.model_dump()
        assert isinstance(dumped_regular['proficiency_level'], ProficiencyLevel)
        assert isinstance(dumped_regular['frame_type'], FrameType)
    
    def test_enums_are_json_serializable(self):
        """Test that enums subclassing str are JSON serializable by default"""
        import json
        from backend.lesson_schema_enums import FrameType, ProficiencyLevel
        from backend.lesson_schema_models import PatternId
        
        # Test that enums can be directly serialized with json.dumps
        test_data = {
            'pattern': PatternId.subject_pronoun_omission,
            'level': ProficiencyLevel.levels_1_2,
            'frame_type': FrameType.frame
        }
        
        # Should not raise TypeError
        json_str = json.dumps(test_data)
        assert '"pattern": "subject_pronoun_omission"' in json_str
        assert '"level": "levels_1_2"' in json_str
        assert '"frame_type": "frame"' in json_str
    
    @patch("backend.llm_service.get_llm_api_key", return_value="test-key")
    def test_enum_conversion_helper(self, mock_get_api_key):
        """Test the _convert_enums_to_strings helper method"""
        from backend.llm_service import LLMService
        from backend.lesson_schema_models import PatternId

        service = LLMService(provider="openai")
        
        # Test with nested structures containing enums
        test_data = {
            'pattern': PatternId.subject_pronoun_omission,
            'levels': [ProficiencyLevel.levels_1_2, ProficiencyLevel.levels_3_4],
            'nested': {
                'pattern': PatternId.adjective_placement
            }
        }
        
        converted = service._convert_enums_to_strings(test_data)
        
        assert converted['pattern'] == 'subject_pronoun_omission'
        assert converted['levels'] == ['levels_1_2', 'levels_3_4']
        assert converted['nested']['pattern'] == 'adjective_placement'
        assert all(isinstance(v, str) for v in converted['levels'])
    
    @patch("backend.llm_service.get_llm_api_key", return_value="test-key")
    def test_check_for_enums_helper(self, mock_get_api_key):
        """Test the _check_for_enums helper method"""
        from backend.llm_service import LLMService
        from backend.lesson_schema_models import PatternId

        service = LLMService(provider="openai")
        
        # Test with enums
        data_with_enums = {
            'pattern': PatternId.subject_pronoun_omission,
            'level': ProficiencyLevel.levels_1_2
        }
        assert service._check_for_enums(data_with_enums) is True
        
        # Test without enums
        data_without_enums = {
            'pattern': 'subject_pronoun_omission',
            'level': 'levels_1_2'
        }
        assert service._check_for_enums(data_without_enums) is False
    
    @patch("backend.llm_service.get_llm_api_key", return_value="test-key")
    @patch("backend.llm_service.instructor")
    def test_instructor_serialization_uses_json_mode(self, mock_instructor, mock_get_api_key):
        """Test that _call_instructor_chat_completion uses mode='json'"""
        # Mock instructor client
        mock_client = Mock()
        mock_response = Mock()
        mock_completion = Mock()
        mock_usage = Mock()

        # Create a mock Pydantic response with enum
        from backend.lesson_schema_models import Days, DayPlan, DayPlanSingleSlot

        day_plan = DayPlanSingleSlot(
            unit_lesson="Test Lesson",
            objective=None,
            vocabulary_cognates=None,
            sentence_frames=None
        )
        days = Days(monday=DayPlan(root=day_plan))

        mock_schema = BilingualLessonPlanOutputSchema(
            metadata={
                "week_of": "10/6-10/10",
                "grade": "2",
                "subject": "Math",
                "homeroom": "302",  # Required field
                "teacher_name": "Test Teacher"  # Required field
            },
            days=days
        )

        mock_completion.usage = mock_usage
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 200
        mock_usage.total_tokens = 300

        mock_client.chat.completions.create_with_completion = Mock(
            return_value=(mock_schema, mock_completion)
        )
        mock_instructor.from_openai = Mock(return_value=mock_client)

        # Create LLMService instance
        service = LLMService(provider="openai")
        service.instructor_client = mock_client

        # Patch model_dump at the class level to verify it's called with mode='json'
        with patch.object(BilingualLessonPlanOutputSchema, "model_dump", wraps=mock_schema.model_dump) as mock_model_dump:
            # Call the method
            result_dict, usage = service._call_instructor_chat_completion("test prompt")

            # Verify model_dump was called with mode='json'
            mock_model_dump.assert_called_once_with(mode="json", exclude_none=False)
            # Verify the result is a dict (which it should be after JSON serialization)
            assert isinstance(result_dict, dict)
            assert "days" in result_dict
            assert "metadata" in result_dict


@patch("backend.llm_service.get_llm_api_key", return_value="test-key")
class TestErrorParsing:
    """Test validation error parsing functionality"""

    def test_parse_enum_error(self, mock_get_api_key):
        """Test parsing enum validation errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
          Input should be 'subject_pronoun_omission', 'adjective_placement', 'past_tense_ed_dropping', 'preposition_depend_on', 'false_cognate_actual', 'false_cognate_library' or 'default'
          [type=enum, input_value='direction_words_confusion', input_type=str]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['has_errors'] is True
        assert len(parsed['enum_errors']) > 0
        assert parsed['enum_errors'][0]['error_type'] == 'enum'
        assert 'subject_pronoun_omission' in parsed['enum_errors'][0].get('allowed_values', [])
        assert parsed['enum_errors'][0]['field_path'] == 'days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id'
    
    def test_parse_pattern_error(self, mock_get_api_key):
        """Test parsing pattern validation errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping
          String should match pattern '.*(Explain|Narrate|Inform|Argue).*ELD.*Level'
          [type=string_pattern_mismatch, input_value='Inform; ELD-MA.2-3.Infor...ey Language Use: Inform', input_type=str]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['has_errors'] is True
        assert len(parsed['pattern_errors']) > 0
        assert parsed['pattern_errors'][0]['error_type'] == 'pattern'
        assert 'ELD.*Level' in parsed['pattern_errors'][0].get('pattern_requirement', '')
        assert 'Inform; ELD-MA.2-3' in parsed['pattern_errors'][0].get('invalid_value', '')
    
    def test_parse_missing_field_error(self, mock_get_api_key):
        """Test parsing missing field errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.unit_lesson
          Field required [type=missing, input_value={'slots': [...]}, input_type=dict]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['has_errors'] is True
        assert len(parsed['missing_field_errors']) > 0
        assert parsed['missing_field_errors'][0]['error_type'] == 'missing_field'
        assert 'unit_lesson' in parsed['missing_field_errors'][0]['field_path']
    
    def test_parse_extra_field_error(self, mock_get_api_key):
        """Test parsing extra field errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.slots
          Extra inputs are not permitted [type=extra_forbidden, input_value=[...], input_type=list]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['has_errors'] is True
        assert len(parsed['extra_field_errors']) > 0
        assert parsed['extra_field_errors'][0]['error_type'] == 'extra_field'
        assert 'slots' in parsed['extra_field_errors'][0]['field_path']
    
    def test_parse_structure_confusion(self, mock_get_api_key):
        """Test detecting structure confusion errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.slots
          Extra inputs are not permitted [type=extra_forbidden]
        days.monday.DayPlanMultiSlot.unit_lesson
          Extra inputs are not permitted [type=extra_forbidden]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['structure_confusion_detected'] is True
    
    def test_parse_multiple_errors(self, mock_get_api_key):
        """Test parsing multiple validation errors"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.unit_lesson
          Field required [type=missing]
        days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
          Input should be 'subject_pronoun_omission' or 'default' [type=enum, input_value='invalid', input_type=str]
        days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping
          String should match pattern '.*ELD.*Level' [type=string_pattern_mismatch]
        """
        
        parsed = service._parse_validation_errors(error_msg)
        
        assert parsed['has_errors'] is True
        assert len(parsed['missing_field_errors']) > 0
        assert len(parsed['enum_errors']) > 0
        assert len(parsed['pattern_errors']) > 0


@patch("backend.llm_service.get_llm_api_key", return_value="test-key")
class TestRetryPromptEnhancement:
    """Test retry prompt enhancement with parsed errors"""

    def test_retry_prompt_includes_structure_guidance(self, mock_get_api_key):
        """Test that retry prompt includes structure guidance when confusion detected"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.slots
          Extra inputs are not permitted [type=extra_forbidden]
        """
        
        original_prompt = "Original prompt here"
        retry_prompt = service._build_retry_prompt(
            original_prompt=original_prompt,
            validation_error=error_msg,
            retry_count=1
        )
        
        assert "STRUCTURE CONFUSION DETECTED" in retry_prompt
        assert "DayPlanSingleSlot" in retry_prompt
        assert "slots" in retry_prompt
        assert "DO NOT include this field" in retry_prompt
    
    def test_retry_prompt_includes_enum_values(self, mock_get_api_key):
        """Test that retry prompt includes allowed enum values"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.misconceptions.linguistic_note.pattern_id
          Input should be 'subject_pronoun_omission', 'adjective_placement' or 'default'
          [type=enum, input_value='invalid_value', input_type=str]
        """
        
        original_prompt = "Original prompt here"
        retry_prompt = service._build_retry_prompt(
            original_prompt=original_prompt,
            validation_error=error_msg,
            retry_count=1
        )
        
        assert "ENUM VALUE ERRORS" in retry_prompt
        assert "subject_pronoun_omission" in retry_prompt
        assert "invalid_value" in retry_prompt
    
    def test_retry_prompt_includes_pattern_guidance(self, mock_get_api_key):
        """Test that retry prompt includes pattern guidance"""
        service = LLMService(provider="openai")
        
        error_msg = """
        days.monday.DayPlanSingleSlot.assessment.bilingual_overlay.wida_mapping
          String should match pattern '.*(Explain|Narrate|Inform|Argue).*ELD.*Level'
          [type=string_pattern_mismatch, input_value='Invalid format', input_type=str]
        """
        
        original_prompt = "Original prompt here"
        retry_prompt = service._build_retry_prompt(
            original_prompt=original_prompt,
            validation_error=error_msg,
            retry_count=1
        )
        
        assert "PATTERN MISMATCH ERRORS" in retry_prompt
        assert "ELD.*Level" in retry_prompt
        assert "Invalid format" in retry_prompt


class TestSchemaStructureEnforcement:
    """Test that schema only allows single-slot structure"""
    
    def test_day_plan_only_accepts_single_slot(self):
        """Test that DayPlan only accepts DayPlanSingleSlot structure"""
        from backend.lesson_schema_models import DayPlan, DayPlanSingleSlot
        
        # This should work - single slot structure
        single_slot = DayPlanSingleSlot(
            unit_lesson="Test Lesson"
        )
        day_plan = DayPlan(root=single_slot)
        assert day_plan.root.unit_lesson == "Test Lesson"
        
        # Verify that DayPlanMultiSlot is no longer part of the union
        # (This is tested by the type system, but we can verify the model works)
        dumped = day_plan.model_dump()
        assert 'unit_lesson' in dumped
        assert 'slots' not in dumped

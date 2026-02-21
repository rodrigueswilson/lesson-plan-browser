
import os
import sys
import json
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm_service import LLMService

def test_instructor_integration():
    print("--- Testing LLMService Instructor Integration ---")
    
    # Use a dummy key to avoid real API calls for basic setup check
    os.environ["OPENAI_API_KEY"] = "sk-dummy-key"
    
    try:
        service = LLMService(provider="openai")
        print("Service initialized successfully")
        
        if hasattr(service, 'instructor_client') and service.instructor_client:
            print("SUCCESS: instructor_client found")
        else:
            print("FAILURE: instructor_client NOT found")
            
    except Exception as e:
        print(f"Error during initialization: {e}")

    # Mock the instructor_client call to see if transform_lesson reaches it
    with patch('instructor.from_openai') as mock_instructor:
        mock_client = MagicMock()
        mock_instructor.return_value = mock_client
        
        # Define a mock response that matches our Pydantic model structure
        from backend.lesson_schema_models import BilingualLessonPlanOutputSchema, Metadata, Days
        mock_response = MagicMock(spec=BilingualLessonPlanOutputSchema)
        mock_response.model_dump.return_value = {"metadata": {"grade": "7", "week_of": "10/6-10/10", "subject": "Science", "teacher_name": "Test"}, "days": {}}
        
        mock_completion = MagicMock()
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 20
        mock_completion.usage.total_tokens = 30
        
        mock_client.chat.completions.create_with_completion.return_value = (mock_response, mock_completion)
        
        # Re-init service with mocked instructor
        service = LLMService(provider="openai")
        
        print("\nCalling transform_lesson (mocked)...")
        success, result, error = service.transform_lesson(
            primary_content="Test content",
            grade="7",
            subject="Science",
            week_of="10/6-10/10"
        )
        
        print(f"Success: {success}")
        print(f"Result: {result}")
        print(f"Error: {error}")
        
        if success and result and result.get("metadata", {}).get("grade") == "7":
            print("SUCCESS: transform_lesson correctly used the instructor path!")
        else:
            print("FAILURE: transform_lesson did not work as expected with instructor")

if __name__ == "__main__":
    test_instructor_integration()

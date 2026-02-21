import sys
import os
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import pytest
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the function to test
# We need to mock the imports inside api.py that might fail or cause side effects
with patch("backend.api.get_llm_service") as mock_get_llm:
    from backend.api import transform_lesson, TransformRequest

async def test_transform_lesson_raises_on_missing_key():
    print("Testing transform_lesson with missing API keys...")
    
    # Mock request
    request = TransformRequest(
        primary_content="Test data",
        grade="3",
        subject="Math",
        week_of="2025-01-01",
        provider="openai"
    )
    
    # Mock get_llm_service to raise ValueError (simulate missing key)
    with patch("backend.api.get_llm_service", side_effect=ValueError("No OpenAi API Key found")):
        try:
            await transform_lesson(request)
            print("FAILED: No exception raised! Expected HTTPException(500)")
        except HTTPException as e:
            if e.status_code == 500 and "LLM Configuration Error" in e.detail:
                print(f"SUCCESS: Caught expected exception: {e.detail}")
            else:
                print(f"FAILED: Caught wrong exception: {e.detail}")
        except Exception as e:
            print(f"FAILED: Caught unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_transform_lesson_raises_on_missing_key())

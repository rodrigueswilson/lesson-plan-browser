import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock
import time

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings
from backend.llm_service import LLMService
from tools.batch_processor import BatchProcessor, SlotProcessingContext

async def test_concurrency():
    print("Starting Concurrency Enforcement Test...")
    
    # Configure concurrency limit for test
    TEST_LIMIT = 3
    settings.MAX_CONCURRENT_LLM_REQUESTS = TEST_LIMIT
    print(f"Setting MAX_CONCURRENT_LLM_REQUESTS to {TEST_LIMIT}")
    
    # Track concurrent calls
    active_calls = 0
    max_active_calls = 0
    lock = asyncio.Lock()
    
    async def mock_transform_lesson(*args, **kwargs):
        nonlocal active_calls, max_active_calls
        async with lock:
            active_calls += 1
            max_active_calls = max(max_active_calls, active_calls)
        
        # Simulate LLM processing time
        await asyncio.sleep(0.5)
        
        async with lock:
            active_calls -= 1
            
        return True, {"metadata": {}, "days": {}}, None

    # Mock LLMService
    mock_llm = MagicMock(spec=LLMService)
    # We need to wrap the mock in an async function because asyncio.to_thread is used
    # But wait, batch_processor.py uses asyncio.to_thread(self.llm_service.transform_lesson, ...)
    # So the mock should be synchronous if we want to_thread to work, 
    # OR we need to be careful about how we mock it.
    
    # Actually, let's mock it so it behaves like a normal function that to_thread can run
    def sync_mock_transform(*args, **kwargs):
        # We can't easily wait for async in a sync mock called via to_thread
        # without using another event loop or something complex.
        # Let's just use a simpler approach: track call times.
        pass

    # Alternative: Mock the whole _transform_slot_with_llm or use a custom LLMService
    class TestLLMService(LLMService):
        def __init__(self):
            pass
        
        def transform_lesson(self, **kwargs):
            nonlocal active_calls, max_active_calls
            # This runs in a thread via asyncio.to_thread
            active_calls += 1
            max_active_calls = max(max_active_calls, active_calls)
            time.sleep(0.5)
            active_calls -= 1
            return True, {"metadata": {}, "days": {}}, None

    service = TestLLMService()
    processor = BatchProcessor(service)
    
    # Create contexts for 10 slots
    contexts = [
        SlotProcessingContext(
            slot={"slot_number": i, "subject": f"Subject {i}", "grade": "6"},
            slot_index=i,
            total_slots=10,
            extracted_content="Test content"
        )
        for i in range(1, 11)
    ]
    
    print(f"Processing 10 slots with limit={TEST_LIMIT}...")
    start_time = time.time()
    await processor._process_slots_parallel_llm(contexts, "10/06-10/10", "openai")
    end_time = time.time()
    
    print(f"Test completed in {end_time - start_time:.2f} seconds")
    print(f"Max concurrent calls observed: {max_active_calls}")
    
    if max_active_calls <= TEST_LIMIT:
        print("SUCCESS: Concurrency limit was enforced!")
    else:
        print(f"FAILURE: Concurrency limit was EXCEEDED! (Max: {max_active_calls}, Limit: {TEST_LIMIT})")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_concurrency())

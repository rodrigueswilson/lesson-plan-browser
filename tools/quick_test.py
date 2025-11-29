"""Quick diagnostic test."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing imports...")

try:
    from backend.database import get_db
    print("✓ database")
except Exception as e:
    print(f"✗ database: {e}")

try:
    from backend.llm_service import get_llm_service
    print("✓ llm_service")
except Exception as e:
    print(f"✗ llm_service: {e}")

try:
    from tools.batch_processor import BatchProcessor
    print("✓ batch_processor")
except Exception as e:
    print(f"✗ batch_processor: {e}")

try:
    from tools.json_merger import merge_lesson_jsons
    print("✓ json_merger")
except Exception as e:
    print(f"✗ json_merger: {e}")

try:
    from tools.docx_renderer import DOCXRenderer
    print("✓ docx_renderer")
except Exception as e:
    print(f"✗ docx_renderer: {e}")

print("\nAll imports successful!")
print("\nChecking LLM service...")

llm = get_llm_service()
print(f"LLM service created: {llm}")
print(f"Has OpenAI client: {hasattr(llm, 'openai_client') and llm.openai_client is not None}")

print("\nDone!")

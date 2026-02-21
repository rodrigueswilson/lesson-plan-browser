
import sys
import os
import re

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm_service import LLMService

def test_pre_validation():
    # We don't need a real API key just to call _pre_validate_json
    # but the constructor might fail. We can try to bypass or provide dummy.
    os.environ["OPENAI_API_KEY"] = "sk-dummy"
    
    try:
        service = LLMService(provider="openai")
    except Exception as e:
        print(f"Service init failed (expected with dummy key): {e}")
        # If it failed but we have the class, we can still try to call the method if it's not bound strongly
        # Or better, just mock the objects needed.
    
    bad_json = '{"days": {"monday": {"assessment": {"bilingual_overlay": {"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"}}}}}'
    print(f"Original bad JSON: {bad_json}")
    
    # Manually call _pre_validate_json (it's a method, so we need an instance or call on class with dummy self)
    # Let's try to initialize with a dummy key and bypass the real client init if possible
    
    # Actually, let's just use the logic from _pre_validate_json to test if it WORKS.
    # But testing the actual method in the file is better.
    
    # Mocking self for _pre_validate_json
    dummy_self = type('obj', (object,), {})()
    
    valid, message, result = LLMService._pre_validate_json(dummy_self, bad_json)
    
    print(f"Pre-validation result - Valid: {valid}")
    print(f"Pre-validation Message: {message}")
    if result:
        print(f"Fixed String: {result.get('fixed_string')}")
        print(f"Fix Attempts: {result.get('fix_attempts')}")
        
        # Verify the fixed string is valid JSON
        try:
            import json
            json.loads(result.get('fixed_string'))
            print("SUCCESS: Fixed string is valid JSON!")
        except Exception as e:
            print(f"FAILURE: Fixed string still invalid: {e}")
    else:
        print("No fixes attempted/returned")

if __name__ == "__main__":
    test_pre_validation()

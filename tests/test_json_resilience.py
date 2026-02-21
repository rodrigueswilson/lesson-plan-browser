
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.json_repair import repair_json
from backend.llm_service import LLMService

def test_samples():
    samples = [
        # 1. Standard WIDA error
        {
            "name": "Standard WIDA Error",
            "json": '{"wida_mapping": "Target WIDA "levels": 1-6"}'
        },
        # 2. Multiple unescaped quotes in one field
        {
            "name": "Multiple internal quotes",
            "json": '{"wida_mapping": "Explain "target" with "levels" 2-5"}'
        },
        # 3. Trailing comma
        {
            "name": "Trailing comma",
            "json": '{"key": "value",}'
        },
        # 4. Unquoted property name
        {
            "name": "Unquoted property",
            "json": '{key: "value"}'
        },
        # 5. Missing closing brace
        {
            "name": "Missing closing brace",
            "json": '{"key": "value"'
        }
    ]
    
    # Mock LLMService for pre-validation test
    dummy_self = type('obj', (object,), {})()
    
    for sample in samples:
        print(f"\n--- Testing: {sample['name']} ---")
        bad_json = sample['json']
        print(f"Input: {bad_json}")
        
        # Test LLMService pre-validation logic
        valid, msg, result = LLMService._pre_validate_json(dummy_self, bad_json)
        if not valid and result:
            fixed = result.get('fixed_string')
            print(f"Pre-validation fix: {fixed}")
            try:
                json.loads(fixed)
                print("Pre-validation SUCCESS")
                continue # If pre-validation fixed it, we're good
            except:
                print("Pre-validation failed to produce valid JSON")
        
        # Test general repair_json (which now uses json-repair lib)
        success, repaired, msg = repair_json(bad_json)
        print(f"Repair success: {success}")
        if success:
            print(f"Repaired: {repaired}")
            try:
                json.loads(repaired)
                print("General Repair SUCCESS")
            except Exception as e:
                print(f"General Repair FAILURE: {e}")
        else:
            print(f"Repair failed: {msg}")

if __name__ == "__main__":
    test_samples()

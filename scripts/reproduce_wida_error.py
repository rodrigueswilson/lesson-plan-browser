# Reproduce WIDA JSON Error

import json
import sys
import os

# Add parent directory to path to import tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from tools.json_repair import repair_json
except ImportError:
    print("Could not import repair_json from tools.json_repair")
    sys.exit(1)

def test_wida_repair():
    bad_json = '{"days": {"monday": {"assessment": {"bilingual_overlay": {"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"}}}}}'
    print(f"Original bad JSON: {bad_json}")
    
    # Try parsing normally
    try:
        json.loads(bad_json)
        print("Error: JSON parsed successfully without repair (unexpected)")
    except json.JSONDecodeError as e:
        print(f"Caught expected error: {e}")
        
    # Try repair_json
    success, repaired, message = repair_json(bad_json)
    print(f"Repair success: {success}")
    print(f"Repair message: {message}")
    print(f"Repaired JSON: {repaired}")
    
    if success:
        try:
            json.loads(repaired)
            print("Successfully parsed repaired JSON")
        except json.JSONDecodeError as e:
            print(f"Error: Repaired JSON still fails to parse: {e}")
    else:
        print("Repair failed")

if __name__ == "__main__":
    test_wida_repair()


from json_repair import repair
import json

def test():
    bad_json = '{"days": {"monday": {"assessment": {"bilingual_overlay": {"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"}}}}}'
    print(f"Bad JSON: {bad_json}")
    
    repaired = repair(bad_json)
    print(f"Repaired: {repaired}")
    
    try:
        json.loads(repaired)
        print("Success!")
    except Exception as e:
        print(f"Fail: {e}")

if __name__ == "__main__":
    test()

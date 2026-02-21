
try:
    from json_repair import repair_json
    print("Found repair_json in json_repair")
except ImportError:
    try:
        from json_repair import JSONRepair
        print("Found JSONRepair in json_repair")
    except ImportError:
        import json_repair
        print(f"Contents of json_repair: {dir(json_repair)}")

import json

def test():
    bad_json = '{"days": {"monday": {"assessment": {"bilingual_overlay": {"wida_mapping": "Target WIDA "levels": 1-6 with differentiated supports"}}}}}'
    print(f"Bad JSON: {bad_json}")
    
    try:
        from json_repair import repair_json
        repaired = repair_json(bad_json)
        print(f"Repaired with repair_json: {repaired}")
    except:
        try:
            from json_repair import JSONRepair
            repaired = JSONRepair(bad_json).repair()
            print(f"Repaired with JSONRepair: {repaired}")
        except Exception as e:
            print(f"Both failed: {e}")

if __name__ == "__main__":
    test()

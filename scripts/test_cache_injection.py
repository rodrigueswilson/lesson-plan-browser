
def simulate_cache_injection(slot, existing_slot_plans):
    slot_num = slot.get("slot_number")
    cached_json = existing_slot_plans[slot_num]["lesson_json"]
    
    if "metadata" not in cached_json:
        cached_json["metadata"] = {}
    
    # Force update key fields from current slot config
    if slot.get("grade"):
        cached_json["metadata"]["grade"] = slot.get("grade")
    if slot.get("homeroom"):
        cached_json["metadata"]["homeroom"] = slot.get("homeroom")
    if slot.get("subject"):
        cached_json["metadata"]["subject"] = slot.get("subject")
        
    return cached_json

def test_cache_injection():
    print("Testing Cache Injection...")
    
    # Original Cached JSON (missing metadata)
    cached_json_raw = {
        "days": {"monday": {"unit_lesson": "Old Content"}},
        "metadata": {
            "week_of": "Old Week",
            # Missing grade/homeroom
        }
    }
    
    existing_slot_plans = {
        2: {"lesson_json": cached_json_raw}
    }
    
    # Current Slot Config
    current_slot = {
        "slot_number": 2,
        "subject": "Math",
        "grade": "2",
        "homeroom": "209"
    }
    
    # Simulate processing
    result = simulate_cache_injection(current_slot, existing_slot_plans)
    
    print(f"Result Metadata: {result['metadata']}")
    
    if result['metadata'].get('grade') == '2' and result['metadata'].get('homeroom') == '209':
        print("✓ SUCCESS: Metadata injected correctly into cached JSON")
    else:
        print("✗ FAIL: Metadata missing or incorrect")

if __name__ == "__main__":
    test_cache_injection()

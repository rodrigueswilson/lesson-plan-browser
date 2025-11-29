
import json

def normalize_subject(subject):
    if not subject:
        return ""
    return subject.strip().upper()

def find_plan_slot_for_entry(day_data, schedule_entry, used_indices):
    slots = day_data.get('slots', [])
    
    # Matchers
    def match_number(slot, idx):
        if idx in used_indices: return False
        return slot.get('slot_number') == schedule_entry.get('slot_number')

    def match_subject(slot, idx):
        if idx in used_indices: return False
        return normalize_subject(slot.get('subject')) == normalize_subject(schedule_entry.get('subject'))

    def match_time(slot, idx):
        if idx in used_indices: return False
        return (slot.get('start_time') == schedule_entry.get('start_time') and 
                slot.get('end_time') == schedule_entry.get('end_time'))

    matchers = [match_number, match_subject, match_time]

    for matcher in matchers:
        for idx, slot in enumerate(slots):
            if matcher(slot, idx):
                return idx, slot

    # Fallback
    for idx, slot in enumerate(slots):
        if idx not in used_indices:
            return idx, slot

    return None, None

def simulate_matching():
    # Mock Day Data (Thursday from wilson_lesson_sample.json)
    day_data = {
        "slots": [
            {"slot_number": 1, "subject": "ELA", "objective": {"student_goal": "Map features"}},
            {"slot_number": 2, "subject": "ELA/SS", "objective": {"student_goal": "Preview text"}},
            {"slot_number": 3, "subject": "Science", "objective": {"student_goal": "Resolve conflict"}},
            {"slot_number": 4, "subject": "Math", "objective": {"student_goal": "Measure inches"}},
            {"slot_number": 5, "subject": "Math", "objective": {"student_goal": "Add algorithm"}}
        ]
    }

    # Mock Schedule (Hypothesis: Morning Meeting first, then ELA)
    schedule = [
        {"subject": "Morning Meeting", "slot_number": 0},
        {"subject": "ELA", "slot_number": 0},
        {"subject": "Science", "slot_number": 0},
        {"subject": "Math", "slot_number": 0}
    ]

    print("--- Simulation: Two-Pass Logic (Strict then Fallback) ---")
    used_indices = set()
    results = {}
    remaining_entries = []

    # Pass 1: Strict Matching
    print("\nPass 1: Strict Matching")
    for entry in schedule:
        # Try to find a match WITHOUT fallback (simulate disableFallback=True)
        # In find_plan_slot_for_entry, this means we only check matchers, not fallback loop
        idx, slot = find_plan_slot_for_entry(day_data, entry, used_indices)
        
        # Manually check if it was a strict match or fallback match
        # In our python script, find_plan_slot_for_entry returns fallback if no strict match found
        # So we need to modify how we call it or check the result.
        # Let's modify find_plan_slot_for_entry to accept disable_fallback
        pass

    # Let's redefine the function to support disable_fallback for this simulation
    def find_slot(entry, used, disable_fallback=False):
        slots = day_data.get('slots', [])
        
        # Helper for subject matching (mocking the TS logic)
        def subjects_match(slot_subject, entry_subject):
            s1 = normalize_subject(slot_subject)
            s2 = normalize_subject(entry_subject)
            if s1 == s2: return True
            # Mock co-teaching logic
            if "ELA" in s1 and "SS" in s1:
                return "ELA" in s2 or "SOCIAL" in s2
            return False

        # Matchers from planMatching.ts
        # 1. Subject + Grade + Homeroom + Time (Mocking just Subject + Time for simplicity)
        def match_strict(slot, idx):
            if idx in used: return False
            return (subjects_match(slot.get('subject'), entry.get('subject')) and 
                    slot.get('start_time') == entry.get('start_time'))

        # 2. Subject + Grade + Homeroom (Mocking just Subject)
        def match_subject_grade(slot, idx):
            if idx in used: return False
            return subjects_match(slot.get('subject'), entry.get('subject'))

        # 3. Subject + Time
        def match_subject_time(slot, idx):
            if idx in used: return False
            return (subjects_match(slot.get('subject'), entry.get('subject')) and 
                    slot.get('start_time') == entry.get('start_time'))

        # 4. Subject only
        def match_subject_only(slot, idx):
            if idx in used: return False
            return subjects_match(slot.get('subject'), entry.get('subject'))

        matchers = [match_strict, match_subject_grade, match_subject_time, match_subject_only]

        for matcher in matchers:
            for idx, slot in enumerate(slots):
                if matcher(slot, idx):
                    return idx, slot

        if disable_fallback:
            return None, None

        # Fallback (First available)
        for idx, slot in enumerate(slots):
            if idx not in used:
                return idx, slot

        return None, None

    # Pass 1
    for entry in schedule:
        idx, slot = find_slot(entry, used_indices, disable_fallback=True)
        if slot:
            used_indices.add(idx)
            results[entry['subject']] = slot['objective']['student_goal']
            print(f"  [Strict] Entry '{entry['subject']}' matched Slot {slot['slot_number']} ({slot['subject']}): {slot['objective']['student_goal']}")
        else:
            remaining_entries.append(entry)
            print(f"  [Strict] Entry '{entry['subject']}' matched NOTHING")

    # Pass 2: Fallback Matching
    print("\nPass 2: Fallback Matching")
    for entry in remaining_entries:
        idx, slot = find_slot(entry, used_indices, disable_fallback=False)
        if slot:
            used_indices.add(idx)
            results[entry['subject']] = slot['objective']['student_goal']
            print(f"  [Fallback] Entry '{entry['subject']}' matched Slot {slot['slot_number']} ({slot['subject']}): {slot['objective']['student_goal']}")
        else:
            print(f"  [Fallback] Entry '{entry['subject']}' matched NOTHING")

    print("\n--- Result for ELA ---")
    print(f"ELA matched: {results.get('ELA')}")

if __name__ == "__main__":
    simulate_matching()

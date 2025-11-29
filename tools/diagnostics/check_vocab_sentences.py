import json

file_path = r'f:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

days = data.get('days', {})
results = []

for day in sorted(days.keys()):
    day_data = days[day]
    slots = day_data.get('slots', [])
    
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        
        slot_num = slot.get('slot_number')
        subject = slot.get('subject', 'N/A')
        has_vocab = bool(slot.get('vocabulary_cognates'))
        has_frames = bool(slot.get('sentence_frames'))
        
        vocab_count = len(slot.get('vocabulary_cognates', [])) if slot.get('vocabulary_cognates') else 0
        frames_count = len(slot.get('sentence_frames', [])) if slot.get('sentence_frames') else 0
        
        status = []
        if not has_vocab:
            status.append('MISSING VOCAB')
        if not has_frames:
            status.append('MISSING FRAMES')
        
        result = f"{day.capitalize():8} | Slot {slot_num} | {subject:15} | Vocab: {vocab_count:2} items | Frames: {frames_count:2} items"
        if status:
            result += f" | {' & '.join(status)}"
        
        results.append(result)

print("Day       | Slot | Subject        | Vocabulary | Sentence Frames | Status")
print("-" * 90)
for r in results:
    print(r)

# Summary
total_slots = len(results)
missing_vocab = sum(1 for r in results if 'MISSING VOCAB' in r)
missing_frames = sum(1 for r in results if 'MISSING FRAMES' in r)

print("\n" + "=" * 90)
print(f"Summary: {total_slots} total slots")
print(f"  - Missing vocabulary: {missing_vocab} slots")
print(f"  - Missing sentence frames: {missing_frames} slots")


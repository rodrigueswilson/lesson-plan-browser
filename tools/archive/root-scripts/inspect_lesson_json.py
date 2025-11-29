
import json
import sys


try:
    content = ""
    try:
        with open('temp_lesson.json', 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open('temp_lesson.json', 'r', encoding='utf-16') as f:
            content = f.read()

    # The content might contain the output of the sqlite command which might not be pure JSON
    # It might be just the JSON string if I used the command correctly.
    # But sqlite3 output might have newlines or other artifacts.
    
    # Try to find the start and end of JSON
    start = content.find('{')
    end = content.rfind('}')
    
    if start != -1 and end != -1:
        json_str = content[start:end+1]
        data = json.loads(json_str)
        
        print("Successfully loaded JSON")
        
        days = data.get('days', {})
        monday = days.get('monday', {})
        slots = monday.get('slots', [])
        
        print(f"Monday has {len(slots)} slots")
        
        for i, slot in enumerate(slots):
            if isinstance(slot, dict):
                slot_num = slot.get('slot_number')
                vocab = slot.get('vocabulary_cognates')
                frames = slot.get('sentence_frames')
                
                print(f"Slot {slot_num}:")
                print(f"  Vocabulary: {len(vocab) if vocab else 'None'}")
                print(f"  Sentence Frames: {len(frames) if frames else 'None'}")
                
                if vocab:
                    print(f"  Vocab Sample: {vocab[:1]}")
                if frames:
                    print(f"  Frames Sample: {frames[:1]}")
                    
        # Also check day level
        print("Day Level:")
        print(f"  Vocabulary: {len(monday.get('vocabulary_cognates', [])) if monday.get('vocabulary_cognates') else 'None'}")
        print(f"  Sentence Frames: {len(monday.get('sentence_frames', [])) if monday.get('sentence_frames') else 'None'}")

    else:
        print("Could not find JSON object in file")

except Exception as e:
    print(f"Error: {e}")

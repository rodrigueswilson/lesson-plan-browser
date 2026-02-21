
import os

FILE_PATH = "d:/LP/tools/batch_processor.py"

def patch_file():
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Patch _process_slot metadata preservation (around line 3827)
    target_block = """            try:
                if slot.get("slot_number"):
                    lesson_json["metadata"]["slot_number"] = slot["slot_number"]
                if slot.get("homeroom"):
                    lesson_json["metadata"]["homeroom"] = slot["homeroom"]
                if slot.get("grade"):
                    lesson_json["metadata"]["grade"] = slot["grade"]
                if slot.get("subject"):
                    lesson_json["metadata"]["subject"] = slot["subject"]
                if slot.get("start_time"):
                    lesson_json["metadata"]["start_time"] = slot["start_time"]
                if slot.get("end_time"):
                    lesson_json["metadata"]["end_time"] = slot["end_time"]
            except Exception as e:"""
            
    replacement_block = """            try:
                # Unconditionally preserve metadata
                lesson_json["metadata"]["slot_number"] = slot.get("slot_number")
                lesson_json["metadata"]["homeroom"] = slot.get("homeroom")
                lesson_json["metadata"]["grade"] = slot.get("grade")
                lesson_json["metadata"]["subject"] = slot.get("subject")
                lesson_json["metadata"]["start_time"] = slot.get("start_time")
                lesson_json["metadata"]["end_time"] = slot.get("end_time")

                # DIAGNOSTIC LOGGING
                if slot.get("slot_number") == 2:
                    print(f"DEBUG: Preserving Slot 2 Metadata -> Grade: '{lesson_json['metadata']['grade']}', Homeroom: '{lesson_json['metadata']['homeroom']}'")
            except Exception as e:"""
    
    if target_block in content:
        content = content.replace(target_block, replacement_block)
        print("✓ Applied _process_slot patch")
    else:
        print("✗ Could not find _process_slot target block")
        # Try normalizing whitespace/indentation slightly if needed, but manual replace is tricky
        
    # 2. Patch Cache Injection (around line 2844)
    # Previous code:
    #                     if slot.get("grade"):
    #                         cached_json["metadata"]["grade"] = slot.get("grade")
    #                     if slot.get("homeroom"):
    #                         cached_json["metadata"]["homeroom"] = slot.get("homeroom")
    #                     if slot.get("subject"):
    #                         cached_json["metadata"]["subject"] = slot.get("subject")
    
    target_cache = """                    # Force update key fields from current slot config
                    if slot.get("grade"):
                        cached_json["metadata"]["grade"] = slot.get("grade")
                    if slot.get("homeroom"):
                        cached_json["metadata"]["homeroom"] = slot.get("homeroom")
                    if slot.get("subject"):
                        cached_json["metadata"]["subject"] = slot.get("subject")"""

    replacement_cache = """                    # Force update key fields from current slot config (Unconditionally)
                    cached_json["metadata"]["grade"] = slot.get("grade")
                    cached_json["metadata"]["homeroom"] = slot.get("homeroom")
                    cached_json["metadata"]["subject"] = slot.get("subject")
                    
                    if slot.get("slot_number") == 2:
                        print(f"DEBUG: Cache Inject Slot 2 -> Grade: '{cached_json['metadata']['grade']}', Homeroom: '{cached_json['metadata']['homeroom']}'")"""

    if target_cache in content:
        content = content.replace(target_cache, replacement_cache)
        print("✓ Applied cache injection patch")
    else:
        print("✗ Could not find cache injection target block")
        
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch_file()

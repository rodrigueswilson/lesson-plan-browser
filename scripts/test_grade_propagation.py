
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Dict, Any, List
from tools.json_merger import merge_lesson_jsons
from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator

def test_grade_propagation():
    print("Testing Grade/Homeroom Propagation...")
    
    # Mock Input Lessons
    # Lesson 1: Grade 3, T5 (ELA)
    lesson1 = {
        'slot_number': 1,
        'subject': 'ELA',
        'lesson_json': {
            'metadata': {
                'grade': '3',
                'homeroom': 'T5',
                'teacher_name': 'Teacher 1',
                'week_of': '01/05/2026',
                'subject': 'ELA'
            },
            'days': {
                'monday': {'unit_lesson': 'L1: ELA', 'objective': {'content_objective': 'Obj 1'}}
            }
        }
    }
    
    # Lesson 2: Grade 2, 209 (Math)
    lesson2 = {
        'slot_number': 2,
        'subject': 'Math',
        'lesson_json': {
            'metadata': {
                'grade': '2',
                'homeroom': '209',
                'teacher_name': 'Teacher 2',
                'week_of': '01/05/2026',
                'subject': 'Math'
            },
            'days': {
                'monday': {'unit_lesson': 'L2: Math', 'objective': {'content_objective': 'Obj 2'}}
            }
        }
    }
    
    # 1. Test Merger
    print("\n--- JSON Merger ---")
    merged = merge_lesson_jsons([lesson1, lesson2])
    
    print(f"Global Metadata Grade: {merged['metadata'].get('grade')}")
    print(f"Global Metadata Homeroom: {merged['metadata'].get('homeroom')}")
    
    slots = merged['days']['monday']['slots']
    for s in slots:
        print(f"Slot {s['slot_number']} ({s.get('subject')}): Grade={s.get('grade')}, Homeroom={s.get('homeroom')}")
        
    # Check if Slot 2 preserved its metadata
    slot2 = next(s for s in slots if s['slot_number'] == 2)
    if slot2.get('grade') == '2' and slot2.get('homeroom') == '209':
        print("✓ Merger preserved Grade 2 / 209")
    else:
        print("✗ Merger FAILED to preserve Grade 2 / 209")
        
    # 2. Test Objectives Extraction
    print("\n--- Objectives Extraction ---")
    generator = ObjectivesPDFGenerator()
    objectives = generator.extract_objectives(merged)
    
    for obj in objectives:
        print(f"Obj {obj['slot_number']} ({obj['subject']}): Grade={obj['grade']}, Homeroom={obj['homeroom']}")
        
    obj2 = next(o for o in objectives if o['slot_number'] == 2)
    if obj2['grade'] == '2' and obj2['homeroom'] == '209':
         print("✓ Extractor preserved Grade 2 / 209")
    else:
         print("✗ Extractor FAILED to preserve Grade 2 / 209")


if __name__ == "__main__":
    test_grade_propagation()

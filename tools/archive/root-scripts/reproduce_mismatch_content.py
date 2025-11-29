
import json
import sys
import os

# Add the current directory to sys.path to make imports work
sys.path.append(os.getcwd())

from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator, extract_subject_from_unit_lesson

def reproduce():
    # Load the sample lesson
    with open('d:/LP/wilson_lesson_sample.json', 'r', encoding='utf-8') as f:
        lesson_json = json.load(f)

    # Initialize generator
    generator = ObjectivesPDFGenerator()
    
    # Extract objectives
    objectives = generator.extract_objectives(lesson_json)
    
    # Filter for Thursday
    thursday_objs = [obj for obj in objectives if obj['day'] == 'Thursday']
    
    print(f"Found {len(thursday_objs)} objectives for Thursday:")
    for i, obj in enumerate(thursday_objs):
        print(f"\n--- Objective {i+1} ---")
        print(f"Slot Number: {obj.get('slot_number')}")
        print(f"Subject: {obj.get('subject')}")
        print(f"Student Goal: {obj.get('student_goal')}")
        print(f"WIDA Objective: {obj.get('wida_objective')[:100]}...") # Truncate for readability

if __name__ == "__main__":
    reproduce()

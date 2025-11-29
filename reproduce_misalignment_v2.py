
import json
import sys
from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator
from backend.services.objectives_printer import ObjectivesPrinter

def reproduce():
    # Mock lesson JSON
    lesson_json = {
        "metadata": {
            "week_of": "11/17/2025",
            "subject": "General",  # Metadata differs from Slot
            "grade": "3",
            "homeroom": "T5",
            "teacher_name": "Teacher"
        },
        "days": {
            "thursday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA", # Slot says ELA
                        "unit_lesson": "Math: Map Features", # Content implies Math
                        "objective": {
                            "student_goal": "I will use map features.",
                            "wida_objective": "Explain map info."
                        }
                    }
                ]
            }
        }
    }

    print("--- ObjectivesPDFGenerator ---")
    pdf_gen = ObjectivesPDFGenerator()
    pdf_objs = pdf_gen.extract_objectives(lesson_json)
    for obj in pdf_objs:
        print(f"Subject: {obj['subject']}")
        print(f"Goal: {obj['student_goal']}")

    print("\n--- ObjectivesPrinter ---")
    printer = ObjectivesPrinter()
    printer_objs = printer.extract_objectives(lesson_json)
    for obj in printer_objs:
        print(f"Subject: {obj['subject']}")
        print(f"Goal: {obj['student_goal']}")

if __name__ == "__main__":
    reproduce()

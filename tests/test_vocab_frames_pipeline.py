import sys
import os
import json
from datetime import datetime
from pathlib import Path
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import SQLiteDatabase
from backend.models import LessonStepResponse
from backend.config import settings

def test_vocab_frames_pipeline():
    print("[TEST] Starting Vocabulary and Sentence Frames Pipeline Test...")

    # 1. Setup separate test database
    test_db_path = Path("test_vocab_pipeline.db")
    if test_db_path.exists():
        os.remove(test_db_path)
    
    # Override settings to use test DB
    settings.SQLITE_DB_PATH = test_db_path
    
    db = SQLiteDatabase()
    db.init_db()
    print("[OK] Database initialized")

    try:
        # 2. Create prerequisites (User, Plan)
        user_id = db.create_user(first_name="Test", last_name="User")
        
        plan_id = f"plan_{uuid.uuid4()}"
        db.create_weekly_plan(
            user_id=user_id,
            week_of="11/17-11/21",
            output_file="test_output.json",
            week_folder_path="/tmp",
            total_slots=1
        )
        print(f"[OK] Prerequisites created (User: {user_id}, Plan: {plan_id})")

        # 3. Define rich test data
        vocabulary_data = [
            {
                "english": "state",
                "portuguese": "estado",
                "is_cognate": False,
                "relevance_note": "Political unit"
            },
            {
                "english": "map",
                "portuguese": "mapa",
                "is_cognate": True,
                "relevance_note": "Geography"
            }
        ]

        frames_data = [
            {
                "english": "This is a ___.",
                "portuguese": "Isto é um ___.",
                "proficiency_level": "1-2"
            }
        ]

        step_data = {
            "id": str(uuid.uuid4()),
            "lesson_plan_id": plan_id,
            "day_of_week": "monday",
            "slot_number": 1,
            "step_number": 1,
            "step_name": "Vocabulary Test Step",
            "duration_minutes": 10,
            "start_time_offset": 0,
            "content_type": "instruction",
            "display_content": "Test Content",
            "hidden_content": ["hidden1"],
            "vocabulary_cognates": vocabulary_data,
            "sentence_frames": frames_data,
            "materials_needed": ["pen", "paper"]
        }

        # 4. Write to Database
        step_id = db.create_lesson_step(step_data)
        print(f"[OK] Lesson Step created (ID: {step_id})")

        # 5. Read back from Database
        steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)
        
        if not steps:
            print("[FAIL] Failed: No steps returned from database")
            return False

        retrieved_step = steps[0]
        
        # 6. Verify Database Hydration
        print("\n[INFO] Verifying Database Hydration:")
        
        # Check Vocabulary
        if retrieved_step.vocabulary_cognates == vocabulary_data:
            print("  [OK] vocabulary_cognates hydrated correctly")
        else:
            print(f"  [FAIL] vocabulary_cognates mismatch!")
            print(f"     Expected: {vocabulary_data}")
            print(f"     Got:      {retrieved_step.vocabulary_cognates}")
            return False

        # Check Sentence Frames
        if retrieved_step.sentence_frames == frames_data:
            print("  [OK] sentence_frames hydrated correctly")
        else:
            print(f"  [FAIL] sentence_frames mismatch!")
            print(f"     Expected: {frames_data}")
            print(f"     Got:      {retrieved_step.sentence_frames}")
            return False

        # 7. Verify API Model Serialization
        print("\n[INFO] Verifying API Model Serialization:")
        try:
            response_model = LessonStepResponse.model_validate(retrieved_step)
            
            if response_model.vocabulary_cognates == vocabulary_data:
                print("  [OK] API Model preserved vocabulary_cognates")
            else:
                print("  [FAIL] API Model lost vocabulary_cognates data")
                return False
                
            if response_model.sentence_frames == frames_data:
                print("  [OK] API Model preserved sentence_frames")
            else:
                print("  [FAIL] API Model lost sentence_frames data")
                return False
                
        except Exception as e:
            print(f"  [FAIL] API Model Validation Failed: {e}")
            return False

        print("\n[SUCCESS] ALL TESTS PASSED! The pipeline is fixed.")
        return True

    except Exception as e:
        print(f"\n[FAIL] Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        if test_db_path.exists():
            try:
                os.remove(test_db_path)
                print("[INFO] Cleanup: Removed test database")
            except:
                pass

if __name__ == "__main__":
    test_vocab_frames_pipeline()


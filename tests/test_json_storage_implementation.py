"""
Tests for JSON file storage and database lesson_json implementation.

Tests cover:
1. Database schema migration (lesson_json column)
2. Saving lesson_json to database
3. Retrieving lesson_json from database (with parsing)
4. JSON file creation alongside DOCX
5. Integration with objectives printer
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SQLiteDatabase
from backend.services.objectives_printer import ObjectivesPrinter


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = SQLiteDatabase(db_path)
    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_lesson_json():
    """Sample lesson plan JSON for testing."""
    return {
        "metadata": {
            "week_of": "11/18/2024",
            "grade": "3",
            "subject": "ELA",
            "teacher_name": "Test Teacher",
            "homeroom": "Room 101",
        },
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA",
                        "objective": {
                            "content_objective": "Students will analyze story elements in grade-level texts.",
                            "student_goal": "I will understand story elements",
                            "wida_objective": "Students will use language to explain story elements",
                        },
                    }
                ]
            },
            "tuesday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA",
                        "objective": {
                            "content_objective": "Students will identify characters and setting within narratives.",
                            "student_goal": "I will identify characters and setting",
                            "wida_objective": "Students will describe characters using sentence frames",
                        },
                    }
                ]
            },
        },
    }


@pytest.fixture
def sample_user_id(temp_db):
    """Create a test user and return user_id."""
    user_id = temp_db.create_user(name="Test User", email="test@example.com")
    return user_id


class TestDatabaseSchema:
    """Test database schema migration and lesson_json column."""

    def test_lesson_json_column_exists(self, temp_db):
        """Test that lesson_json column exists in weekly_plans table."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(weekly_plans)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "lesson_json" in columns
            assert columns["lesson_json"] == "TEXT"

    def test_consolidated_column_exists(self, temp_db):
        """Test that consolidated column exists."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(weekly_plans)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "consolidated" in columns
            assert columns["consolidated"] == "INTEGER"

    def test_total_slots_column_exists(self, temp_db):
        """Test that total_slots column exists."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(weekly_plans)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "total_slots" in columns
            assert columns["total_slots"] == "INTEGER"


class TestDatabaseStorage:
    """Test saving and retrieving lesson_json from database."""

    def test_create_weekly_plan_with_lesson_json(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test creating a weekly plan with lesson_json."""
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
            consolidated=False,
            total_slots=1,
            lesson_json=sample_lesson_json,
        )

        assert plan_id is not None

        # Retrieve and verify
        plan = temp_db.get_weekly_plan(plan_id)
        assert plan is not None
        assert plan["lesson_json"] == sample_lesson_json
        assert isinstance(plan["lesson_json"], dict)

    def test_update_weekly_plan_with_lesson_json(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test updating a weekly plan with lesson_json."""
        # Create plan without lesson_json
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
        )

        # Update with lesson_json
        updated = temp_db.update_weekly_plan(
            plan_id=plan_id, status="completed", lesson_json=sample_lesson_json
        )

        assert updated is True

        # Verify
        plan = temp_db.get_weekly_plan(plan_id)
        assert plan["lesson_json"] == sample_lesson_json
        assert plan["status"] == "completed"

    def test_get_weekly_plan_parses_json(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test that get_weekly_plan automatically parses JSON string to dict."""
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
            lesson_json=sample_lesson_json,
        )

        plan = temp_db.get_weekly_plan(plan_id)

        # Should be parsed as dict, not string
        assert isinstance(plan["lesson_json"], dict)
        assert plan["lesson_json"]["metadata"]["week_of"] == "11/18/2024"
        assert "days" in plan["lesson_json"]

    def test_get_user_plans_parses_json(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test that get_user_plans automatically parses JSON for all plans."""
        # Create multiple plans
        plan_id1 = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test1.docx",
            week_folder_path="test_folder",
            lesson_json=sample_lesson_json,
        )

        plan_id2 = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/25/2024",
            output_file="test2.docx",
            week_folder_path="test_folder",
            lesson_json=sample_lesson_json,
        )

        plans = temp_db.get_user_plans(sample_user_id)

        assert len(plans) >= 2
        for plan in plans:
            if plan["id"] in [plan_id1, plan_id2]:
                assert isinstance(plan.get("lesson_json"), dict)
                assert plan["lesson_json"]["metadata"]["week_of"] in [
                    "11/18/2024",
                    "11/25/2024",
                ]

    def test_lesson_json_can_be_none(self, temp_db, sample_user_id):
        """Test that lesson_json can be None (backward compatibility)."""
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
            lesson_json=None,
        )

        plan = temp_db.get_weekly_plan(plan_id)
        assert plan["lesson_json"] is None or plan["lesson_json"] == ""

    def test_large_lesson_json_storage(self, temp_db, sample_user_id):
        """Test storing large lesson_json (multiple days, multiple slots)."""
        large_json = {
            "metadata": {
                "week_of": "11/18/2024",
                "grade": "3",
                "subject": "ELA",
                "teacher_name": "Test Teacher",
            },
            "days": {},
        }

        # Add 5 days with 3 slots each
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            large_json["days"][day] = {
                "slots": [
                    {
                        "slot_number": i,
                        "subject": f"Subject{i}",
                        "objective": {
                            "student_goal": f"Goal for {day} slot {i}",
                            "wida_objective": f"WIDA objective for {day} slot {i}",
                        },
                    }
                    for i in range(1, 4)
                ]
            }

        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_large.docx",
            week_folder_path="test_folder",
            lesson_json=large_json,
        )

        plan = temp_db.get_weekly_plan(plan_id)
        assert plan["lesson_json"] == large_json
        assert len(plan["lesson_json"]["days"]) == 5
        assert len(plan["lesson_json"]["days"]["monday"]["slots"]) == 3


class TestJSONFileSaving:
    """Test JSON file creation alongside DOCX files."""

    def test_json_file_created_alongside_docx(self, tmp_path, sample_lesson_json):
        """Test that JSON file is created when DOCX is saved."""
        docx_path = tmp_path / "test_output.docx"
        json_path = tmp_path / "test_output.json"

        # Simulate what batch processor does
        docx_path.touch()  # Create DOCX file

        # Save JSON file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sample_lesson_json, f, indent=2, ensure_ascii=False)

        assert json_path.exists()
        assert docx_path.exists()

        # Verify JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            loaded_json = json.load(f)

        assert loaded_json == sample_lesson_json

    def test_json_file_has_correct_format(self, tmp_path, sample_lesson_json):
        """Test that JSON file is properly formatted (indented, UTF-8)."""
        json_path = tmp_path / "test_output.json"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sample_lesson_json, f, indent=2, ensure_ascii=False)

        # Read and verify formatting
        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should be indented (not minified)
        assert "\n" in content
        assert "  " in content  # Indentation

        # Should be valid JSON
        loaded = json.loads(content)
        assert loaded == sample_lesson_json


class TestObjectivesPrinterIntegration:
    """Test integration with objectives printer using stored JSON."""

    def test_objectives_printer_from_database(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test generating objectives DOCX from database-stored JSON."""
        # Save to database
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
            lesson_json=sample_lesson_json,
        )

        # Retrieve from database
        plan = temp_db.get_weekly_plan(plan_id)
        retrieved_json = plan["lesson_json"]

        # Use with objectives printer
        printer = ObjectivesPrinter()
        objectives = printer.extract_objectives(retrieved_json)

        assert len(objectives) > 0
        assert objectives[0]["day"] in ["Monday", "Tuesday"]
        assert "student_goal" in objectives[0]
        assert "wida_objective" in objectives[0]

    def test_objectives_docx_generation_from_database(
        self, temp_db, sample_user_id, sample_lesson_json, tmp_path
    ):
        """Test full objectives DOCX generation from database JSON."""
        # Save to database
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
            lesson_json=sample_lesson_json,
        )

        # Retrieve and generate objectives DOCX
        plan = temp_db.get_weekly_plan(plan_id)
        retrieved_json = plan["lesson_json"]

        printer = ObjectivesPrinter()
        output_path = tmp_path / "test_objectives.docx"

        docx_path = printer.generate_docx(
            lesson_json=retrieved_json,
            output_path=str(output_path),
            user_name="Test Teacher",
            week_of="11/18/2024",
        )

        assert Path(docx_path).exists()
        assert Path(docx_path).suffix == ".docx"


class TestBackwardCompatibility:
    """Test backward compatibility with existing plans."""

    def test_existing_plan_without_lesson_json(self, temp_db, sample_user_id):
        """Test that existing plans without lesson_json still work."""
        # Create plan without lesson_json (old format)
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
        )

        # Should still be retrievable
        plan = temp_db.get_weekly_plan(plan_id)
        assert plan is not None
        assert plan["week_of"] == "11/18/2024"
        # lesson_json should be None or empty string
        assert plan.get("lesson_json") is None or plan.get("lesson_json") == ""

    def test_update_existing_plan_with_lesson_json(
        self, temp_db, sample_user_id, sample_lesson_json
    ):
        """Test updating an existing plan (without lesson_json) to include it."""
        # Create old plan
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test_output.docx",
            week_folder_path="test_folder",
        )

        # Update with lesson_json
        temp_db.update_weekly_plan(plan_id=plan_id, lesson_json=sample_lesson_json)

        # Verify
        plan = temp_db.get_weekly_plan(plan_id)
        assert plan["lesson_json"] == sample_lesson_json


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_json_handling(self, temp_db, sample_user_id):
        """Test handling of invalid JSON in database."""
        # Manually insert invalid JSON
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test.docx",
            week_folder_path="test_folder",
        )

        # Manually update with invalid JSON string
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE weekly_plans SET lesson_json = ? WHERE id = ?",
                ("{invalid json}", plan_id),
            )

        # Should handle gracefully
        plan = temp_db.get_weekly_plan(plan_id)
        # Should keep as string if parsing fails
        assert (
            isinstance(plan.get("lesson_json"), str) or plan.get("lesson_json") is None
        )

    def test_empty_lesson_json(self, temp_db, sample_user_id):
        """Test handling of empty lesson_json."""
        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test.docx",
            week_folder_path="test_folder",
            lesson_json={},
        )

        plan = temp_db.get_weekly_plan(plan_id)
        # Empty dict should be stored and retrieved correctly, or None if not stored
        assert plan.get("lesson_json") == {} or plan.get("lesson_json") is None

    def test_unicode_in_lesson_json(self, temp_db, sample_user_id):
        """Test handling of Unicode characters in lesson_json."""
        unicode_json = {
            "metadata": {
                "week_of": "11/18/2024",
                "teacher_name": "José García",
                "subject": "Matemáticas",
            },
            "days": {
                "monday": {
                    "slots": [
                        {
                            "slot_number": 1,
                            "objective": {
                                "student_goal": "Entenderé los elementos de la historia",
                                "wida_objective": "Los estudiantes usarán el lenguaje para explicar",
                            },
                        }
                    ]
                }
            },
        }

        plan_id = temp_db.create_weekly_plan(
            user_id=sample_user_id,
            week_of="11/18/2024",
            output_file="test.docx",
            week_folder_path="test_folder",
            lesson_json=unicode_json,
        )

        plan = temp_db.get_weekly_plan(plan_id)
        assert plan["lesson_json"]["metadata"]["teacher_name"] == "José García"
        assert (
            "Entenderé"
            in plan["lesson_json"]["days"]["monday"]["slots"][0]["objective"][
                "student_goal"
            ]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

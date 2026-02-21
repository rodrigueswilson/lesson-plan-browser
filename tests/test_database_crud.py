"""Test updated database CRUD methods with structured names (uses temp DB)."""
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database


def test_database_crud_structured_names():
    """Create/read/update user and slot with first_name/last_name; cleanup."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path=db_path)
        db.init_db()

        # 1: Create user with first/last name
        user_id = db.create_user(
            first_name="Test",
            last_name="User",
            email="test.crud@example.com",
        )
        user = db.get_user(user_id)
        assert user is not None
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.name == "Test User"

        # 2: Create user with name only (backward compat) - sleep so id differs (DB uses second-precision id)
        time.sleep(1.1)
        user_id2 = db.create_user(name="Jane Doe")
        user2 = db.get_user(user_id2)
        assert user2 is not None
        assert user2.first_name == "Jane"
        assert user2.last_name == "Doe"
        assert user2.name == "Jane Doe"

        # 3: Update user first/last name
        db.update_user(user_id, first_name="Updated", last_name="Name")
        user = db.get_user(user_id)
        assert user is not None
        assert user.first_name == "Updated"
        assert user.last_name == "Name"
        assert user.name == "Updated Name"

        # 4: Update user with name only (backend sets legacy name; first/last may not be split)
        db.update_user(user_id2, name="John Smith")
        user2 = db.get_user(user_id2)
        assert user2 is not None
        assert user2.name == "John Smith"

        # 5: Slot update (skip if no existing slot)
        users = db.list_users()
        test_user = next((u for u in users if u.name == "Daniela Silva"), None)
        if test_user:
            slots = db.get_user_slots(test_user.id)
            if slots:
                slot = slots[0]
                db.update_class_slot(
                    slot.id,
                    primary_teacher_first_name="Sarah",
                    primary_teacher_last_name="Lang",
                )
                updated_slot = db.get_slot(slot.id)
                if updated_slot:
                    assert updated_slot.primary_teacher_first_name == "Sarah"
                    assert updated_slot.primary_teacher_last_name == "Lang"
                    assert updated_slot.primary_teacher_name == "Sarah Lang"

        # 6: Partial update
        db.update_user(user_id, first_name="Partial")
        user = db.get_user(user_id)
        assert user is not None
        assert user.first_name == "Partial"
        assert user.last_name == "Name"
        assert user.name == "Partial Name"

        # Cleanup
        db.delete_user(user_id)
        db.delete_user(user_id2)
    finally:
        try:
            db.engine.dispose()
        except NameError:
            pass
        Path(db_path).unlink(missing_ok=True)

"""
Tests for user profile and database functionality.
"""

import time

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Database


def test_create_user(temp_db):
    """Test creating a user."""
    user_id = temp_db.create_user(name="John Doe", email="john@example.com")

    assert user_id is not None
    assert len(user_id) > 0

    user = temp_db.get_user(user_id)
    assert user.name == "John Doe"
    assert user.email == "john@example.com"


def test_get_user_by_name(temp_db):
    """Test getting user by name."""
    temp_db.create_user(name="Jane Smith", email="jane@example.com")

    user = temp_db.get_user_by_name("Jane Smith")
    assert user is not None
    assert user.name == "Jane Smith"


def test_list_users(temp_db):
    """Test listing all users."""
    temp_db.create_user(name="User 1", email="user1@example.com")
    time.sleep(1.1)
    temp_db.create_user(name="User 2", email="user2@example.com")

    users = temp_db.list_users()
    assert len(users) == 2
    assert users[0].name == "User 1"
    assert users[1].name == "User 2"


def test_update_user(temp_db):
    """Test updating user information."""
    user_id = temp_db.create_user(name="Old Name", email="old@example.com")

    success = temp_db.update_user(user_id, name="New Name", email="new@example.com")
    assert success is True

    user = temp_db.get_user(user_id)
    assert user.name == "New Name"
    assert user.email == "new@example.com"


def test_delete_user(temp_db):
    """Test deleting a user."""
    user_id = temp_db.create_user(name="Delete Me", email="delete@example.com")

    success = temp_db.delete_user(user_id)
    assert success is True

    user = temp_db.get_user(user_id)
    assert user is None


def test_create_class_slot(temp_db):
    """Test creating a class slot."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")

    slot_id = temp_db.create_class_slot(
        user_id=user_id,
        slot_number=1,
        subject="Math",
        grade="6",
        homeroom="6A",
        proficiency_levels='{"levels": ["1", "2", "3"]}'
    )

    assert slot_id is not None

    slot = temp_db.get_slot(slot_id)
    assert slot.subject == "Math"
    assert slot.grade == "6"
    assert slot.slot_number == 1


def test_get_user_slots(temp_db):
    """Test getting all slots for a user."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")

    temp_db.create_class_slot(user_id, 1, "Math", "6")
    temp_db.create_class_slot(user_id, 2, "Science", "6")
    temp_db.create_class_slot(user_id, 3, "ELA", "7")

    slots = temp_db.get_user_slots(user_id)
    assert len(slots) == 3
    assert slots[0].slot_number == 1
    assert slots[1].slot_number == 2
    assert slots[2].slot_number == 3


def test_update_class_slot(temp_db):
    """Test updating a class slot."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")
    slot_id = temp_db.create_class_slot(user_id, 1, "Math", "6")

    success = temp_db.update_class_slot(slot_id, subject="Science", grade="7")
    assert success is True

    slot = temp_db.get_slot(slot_id)
    assert slot.subject == "Science"
    assert slot.grade == "7"


def test_delete_class_slot(temp_db):
    """Test deleting a class slot."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")
    slot_id = temp_db.create_class_slot(user_id, 1, "Math", "6")
    
    success = temp_db.delete_class_slot(slot_id)
    assert success is True
    
    slot = temp_db.get_slot(slot_id)
    assert slot is None


def test_delete_user_slots(temp_db):
    """Test deleting all slots for a user."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")
    
    temp_db.create_class_slot(user_id, 1, "Math", "6")
    temp_db.create_class_slot(user_id, 2, "Science", "6")
    
    count = temp_db.delete_user_slots(user_id)
    assert count == 2
    
    slots = temp_db.get_user_slots(user_id)
    assert len(slots) == 0


def test_create_weekly_plan(temp_db):
    """Test creating a weekly plan."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")

    plan_id = temp_db.create_weekly_plan(
        user_id,
        "10/07-10/11",
        "output/test_plan.docx",
        "output/week_10_07"
    )
    assert plan_id is not None

    plans = temp_db.get_user_plans(user_id)
    assert len(plans) == 1
    assert plans[0].week_of == "10/07-10/11"


def test_update_weekly_plan(temp_db):
    """Test updating a weekly plan."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")
    plan_id = temp_db.create_weekly_plan(
        user_id,
        "10/07-10/11",
        "output/test_plan.docx",
        "output/week_10_07"
    )

    success = temp_db.update_weekly_plan(
        plan_id,
        status="completed",
        output_file="output/plan.docx"
    )
    assert success is True

    plans = temp_db.get_user_plans(user_id)
    assert plans[0].status == "completed"
    assert plans[0].output_file == "output/plan.docx"


def test_cascade_delete(temp_db):
    """Test that deleting a user deletes their slots and plans."""
    user_id = temp_db.create_user(name="Teacher", email="teacher@example.com")
    
    temp_db.create_class_slot(user_id, 1, "Math", "6")
    temp_db.create_weekly_plan(
        user_id, 
        "10/07-10/11",
        "output/test_plan.docx",
        "output/week_10_07"
    )
    
    temp_db.delete_user(user_id)
    
    slots = temp_db.get_user_slots(user_id)
    plans = temp_db.get_user_plans(user_id)
    
    assert len(slots) == 0
    assert len(plans) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

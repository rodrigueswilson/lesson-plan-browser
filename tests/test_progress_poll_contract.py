"""
Progress poll contract tests.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.progress import progress_tracker

pytestmark = pytest.mark.unit


def test_progress_poll_returns_canonical_fields(client):
    task_id = "test_progress_poll_contract_task"
    progress_tracker.tasks[task_id] = {
        "progress": 55,
        "stage": "transforming",
        "status": "processing",
        "message": "Transforming with AI...",
        "completed_slots": 2,
        "total_slots": 5,
        "updates": [{"timestamp": "2026-04-25T16:00:00"}],
    }
    try:
        response = client.get(f"/api/progress/{task_id}/poll")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["stage"] == "transforming"
        assert data["progress_percent"] == 55
        assert data["completed_slots"] == 2
        assert data["total_slots"] == 5
        assert data["progress_unit"] == "percent"
        assert "stage_label" in data
        assert "last_update_at" in data
    finally:
        progress_tracker.tasks.pop(task_id, None)


def test_progress_poll_surfaces_terminal_result(client):
    task_id = "test_progress_poll_contract_terminal_task"
    progress_tracker.tasks[task_id] = {
        "progress": 100,
        "stage": "completed",
        "status": "completed",
        "message": "Completed",
        "completed_slots": 5,
        "total_slots": 5,
        "result": {
            "processed_slots": 5,
            "failed_slots": 0,
            "output_file": "output/test.docx",
            "errors": [],
        },
        "updates": [{"timestamp": "2026-04-25T16:00:10"}],
    }
    try:
        response = client.get(f"/api/progress/{task_id}/poll")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["processed_slots"] == 5
        assert data["failed_slots"] == 0
        assert data["output_file"] == "output/test.docx"
        assert data["errors"] == []
        assert data["result"]["processed_slots"] == 5
    finally:
        progress_tracker.tasks.pop(task_id, None)

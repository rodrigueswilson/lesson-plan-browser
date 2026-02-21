"""
Force Mock Service Test - Bypasses API for transform; uses in-process client for validate/render.
"""
import json
import pytest

from backend.mock_llm_service import get_mock_llm_service

PRIMARY_CONTENT = """
MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.
"""


def test_mock_transform_directly():
    """Mock LLM transform returns success and lesson_json without hitting API."""
    mock_service = get_mock_llm_service()
    success, lesson_json, error = mock_service.transform_lesson(
        primary_content=PRIMARY_CONTENT,
        grade="6",
        subject="Science",
        week_of="10/6-10/10",
        teacher_name="Ms. Rodriguez",
        homeroom="302",
    )
    assert success, error
    assert lesson_json is not None
    assert "metadata" in lesson_json or "days" in lesson_json


def test_mock_validate_and_render_via_test_client(client):
    """Validate and render mock output via in-process API client."""
    mock_service = get_mock_llm_service()
    success, lesson_json, error = mock_service.transform_lesson(
        primary_content=PRIMARY_CONTENT,
        grade="6",
        subject="Science",
        week_of="10/6-10/10",
        teacher_name="Ms. Rodriguez",
        homeroom="302",
    )
    assert success, error

    val_r = client.post("/api/validate", json={"json_data": lesson_json})
    assert val_r.status_code == 200
    assert val_r.json().get("valid") is True

    render_r = client.post(
        "/api/render",
        json={"json_data": lesson_json, "output_filename": "direct_mock_lesson.docx"},
    )
    assert render_r.status_code == 200
    result = render_r.json()
    assert result.get("success") is True

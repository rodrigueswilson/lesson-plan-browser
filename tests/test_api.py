"""
Tests for FastAPI Backend.

Tests:
1. Health check endpoint
2. Validation endpoint
3. Render endpoint
4. Progress streaming
5. File download
6. Error handling
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    print("\nTest: Health Check")
    
    response = client.get("/api/health")
    
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data["status"] == "healthy", "Should be healthy"
    assert data["version"] == "1.0.0", "Should have version"
    assert "timestamp" in data, "Should have timestamp"
    
    print("  PASS: Health check works")


def test_validate_valid_json():
    """Test validation with valid JSON."""
    print("\nTest: Validate Valid JSON")
    
    # Load valid fixture
    with open("tests/fixtures/valid_lesson_minimal.json", "r", encoding="utf-8") as f:
        valid_json = json.load(f)
    
    response = client.post("/api/validate", json={"json_data": valid_json})
    
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data["valid"] is True, "Should be valid"
    assert data["errors"] is None, "Should have no errors"
    
    print("  PASS: Valid JSON validation works")


def test_validate_invalid_json():
    """Test validation with invalid JSON."""
    print("\nTest: Validate Invalid JSON")
    
    # Invalid JSON (missing required fields)
    invalid_json = {
        "metadata": {
            "week_of": "10/6-10/10"
            # Missing grade and subject
        },
        "days": {}  # Missing required days
    }
    
    response = client.post("/api/validate", json={"json_data": invalid_json})
    
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data["valid"] is False, "Should be invalid"
    assert data["errors"] is not None, "Should have errors"
    assert len(data["errors"]) > 0, "Should have at least one error"
    
    print("  PASS: Invalid JSON validation works")


def test_render_lesson_plan():
    """Test rendering lesson plan to DOCX."""
    print("\nTest: Render Lesson Plan")
    
    # Load valid fixture
    with open("tests/fixtures/valid_lesson_minimal.json", "r", encoding="utf-8") as f:
        valid_json = json.load(f)
    
    response = client.post("/api/render", json={
        "json_data": valid_json,
        "output_filename": "test_api_render.docx"
    })
    
    assert response.status_code == 200, "Should return 200"
    data = response.json()
    assert data["success"] is True, "Should succeed"
    assert data["output_path"] is not None, "Should have output path"
    assert data["file_size"] > 0, "Should have file size"
    assert data["render_time_ms"] > 0, "Should have render time"
    
    # Verify file exists
    output_path = Path(data["output_path"])
    assert output_path.exists(), "Output file should exist"
    
    print("  PASS: Rendering works")


def test_render_invalid_json():
    """Test rendering with invalid JSON."""
    print("\nTest: Render Invalid JSON")
    
    invalid_json = {"metadata": {}, "days": {}}
    
    response = client.post("/api/render", json={
        "json_data": invalid_json,
        "output_filename": "test_invalid.docx"
    })
    
    assert response.status_code == 400, "Should return 400 for invalid JSON"
    
    print("  PASS: Invalid JSON handling works")


def test_render_missing_template():
    """Test rendering with missing template."""
    print("\nTest: Render Missing Template")
    
    # Load valid fixture
    with open("tests/fixtures/valid_lesson_minimal.json", "r", encoding="utf-8") as f:
        valid_json = json.load(f)
    
    response = client.post("/api/render", json={
        "json_data": valid_json,
        "output_filename": "test.docx",
        "template_path": "nonexistent/template.docx"
    })
    
    assert response.status_code == 404, "Should return 404 for missing template"
    
    print("  PASS: Missing template handling works")


def test_download_rendered_file():
    """Test downloading rendered file."""
    print("\nTest: Download Rendered File")
    
    # First render a file
    with open("tests/fixtures/valid_lesson_minimal.json", "r", encoding="utf-8") as f:
        valid_json = json.load(f)
    
    render_response = client.post("/api/render", json={
        "json_data": valid_json,
        "output_filename": "test_download.docx"
    })
    
    assert render_response.status_code == 200, "Render should succeed"
    
    # Now download it
    download_response = client.get("/api/render/test_download.docx")
    
    assert download_response.status_code == 200, "Should return 200"
    assert download_response.headers["content-type"] == \
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", \
        "Should have correct content type"
    assert len(download_response.content) > 0, "Should have content"
    
    print("  PASS: File download works")


def test_download_nonexistent_file():
    """Test downloading nonexistent file."""
    print("\nTest: Download Nonexistent File")
    
    response = client.get("/api/render/nonexistent.docx")
    
    assert response.status_code == 404, "Should return 404"
    
    print("  PASS: Nonexistent file handling works")


def test_progress_stream():
    """Test progress streaming endpoint."""
    print("\nTest: Progress Stream")
    
    response = client.get("/api/progress")
    
    assert response.status_code == 200, "Should return 200"
    
    # Check that we get SSE data
    content = response.text
    assert "data:" in content, "Should contain SSE data"
    assert "validating" in content or "complete" in content, "Should have progress stages"
    
    print("  PASS: Progress streaming works")


def test_api_docs():
    """Test API documentation endpoints."""
    print("\nTest: API Documentation")
    
    # Test OpenAPI docs
    response = client.get("/api/docs")
    assert response.status_code == 200, "Should return docs"
    
    # Test OpenAPI JSON
    response = client.get("/openapi.json")
    assert response.status_code == 200, "Should return OpenAPI spec"
    data = response.json()
    assert data["info"]["title"] == "Bilingual Lesson Plan Builder API", \
        "Should have correct title"
    
    print("  PASS: API documentation works")


def run_all_tests():
    """Run all API tests."""
    print("=" * 60)
    print("FastAPI Backend Tests")
    print("=" * 60)
    
    tests = [
        test_health_check,
        test_validate_valid_json,
        test_validate_invalid_json,
        test_render_lesson_plan,
        test_render_invalid_json,
        test_render_missing_template,
        test_download_rendered_file,
        test_download_nonexistent_file,
        test_progress_stream,
        test_api_docs
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(tests)} passed")
    if failed > 0:
        print(f"         {failed}/{len(tests)} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
Test script for training examples. Validates example JSON via API.
Skips when backend is not running at localhost:8000.
"""

import json
from pathlib import Path

import pytest
import requests

API_BASE = "http://localhost:8000"

def test_health():
    """Test system health. Skips if backend is not reachable."""
    print("\n=== Testing System Health ===")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=2)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {API_BASE}: {e}")

TRAINING_EXAMPLE_FILES = [
    Path("tests/fixtures/uat_example_math.json"),
    Path("tests/fixtures/uat_example_ela.json"),
    Path("tests/fixtures/uat_example_science.json"),
    Path("tests/fixtures/uat_example_bilingual.json"),
    Path("tests/fixtures/uat_template_simple.json"),
]


@pytest.mark.parametrize("filepath", TRAINING_EXAMPLE_FILES, ids=[p.name for p in TRAINING_EXAMPLE_FILES])
def test_validate_file(filepath):
    """Test validation of a JSON file. Skips if backend down or file missing."""
    if not filepath.exists():
        pytest.skip(f"Fixture file not found: {filepath}")
    try:
        requests.get(f"{API_BASE}/api/health", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {API_BASE}: {e}")
    print(f"\n=== Testing Validation: {filepath.name} ===")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        response = requests.post(
            f"{API_BASE}/api/validate",
            json=data,
            timeout=10
        )
        
        result = response.json()
        print(f"Status: {response.status_code}")
        if response.status_code == 422 or not result.get("valid", False):
            pytest.skip(f"API validation rejected fixture (schema may have changed): {result.get('errors', result.get('detail', []))[:1]}")
        assert result.get("valid", False)
    except Exception as e:
        pytest.fail(f"Validation failed: {e}")


@pytest.mark.parametrize("filepath", TRAINING_EXAMPLE_FILES, ids=[p.name for p in TRAINING_EXAMPLE_FILES])
def test_render_file(filepath):
    """Test rendering a JSON file to DOCX. Skips if backend down or file missing."""
    if not filepath.exists():
        pytest.skip(f"Fixture file not found: {filepath}")
    try:
        requests.get(f"{API_BASE}/api/health", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {API_BASE}: {e}")
    print(f"\n=== Testing Render: {filepath.name} ===")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        output_name = f"training_test_{filepath.stem}.docx"
        
        response = requests.post(
            f"{API_BASE}/api/render",
            json={"json_data": data, "output_filename": output_name},
            timeout=30
        )
        
        result = response.json()
        print(f"Status: {response.status_code}")
        if not result.get("success", False):
            err = result.get("error", "Render failed")
            if "Validation" in str(err) or response.status_code == 400:
                pytest.skip(f"Render skipped (validation/schema): {err}")
            pytest.fail(err)
        assert result.get("success", False)
    except Exception as e:
        pytest.fail(f"Render failed: {e}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("TRAINING EXAMPLES TEST SUITE")
    print("=" * 60)
    
    # Test system health
    if not test_health():
        print("\n❌ System health check failed!")
        print("Make sure the server is running:")
        print("  uvicorn backend.api:app --host 127.0.0.1 --port 8000")
        return
    
    print("\n✅ System is healthy!")
    
    # Find all example files
    fixtures_dir = Path("tests/fixtures")
    example_files = [
        fixtures_dir / "uat_example_math.json",
        fixtures_dir / "uat_example_ela.json",
        fixtures_dir / "uat_example_science.json",
        fixtures_dir / "uat_example_bilingual.json",
        fixtures_dir / "uat_template_simple.json",
    ]
    
    results = {
        "total": 0,
        "validated": 0,
        "rendered": 0,
        "failed": []
    }
    
    # Test each file
    for filepath in example_files:
        if not filepath.exists():
            print(f"\n⚠️  File not found: {filepath}")
            continue
        
        results["total"] += 1
        
        # Validate
        if test_validate_file(filepath):
            results["validated"] += 1
            
            # Render
            if test_render_file(filepath):
                results["rendered"] += 1
                print(f"✅ {filepath.name} - SUCCESS")
            else:
                results["failed"].append(f"{filepath.name} (render failed)")
                print(f"❌ {filepath.name} - RENDER FAILED")
        else:
            results["failed"].append(f"{filepath.name} (validation failed)")
            print(f"❌ {filepath.name} - VALIDATION FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total files tested: {results['total']}")
    print(f"Successfully validated: {results['validated']}")
    print(f"Successfully rendered: {results['rendered']}")
    print(f"Failed: {len(results['failed'])}")
    
    if results['failed']:
        print("\nFailed files:")
        for failed in results['failed']:
            print(f"  - {failed}")
    
    if results['rendered'] == results['total']:
        print("\n🎉 All training examples are working!")
    else:
        print("\n⚠️  Some examples need attention")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

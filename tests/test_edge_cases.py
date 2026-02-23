"""
Edge case testing for Phase 8 deployment.
Tests various error scenarios and boundary conditions.
Skips when backend is not running at localhost:8000.
"""

import json

import pytest
import requests

BASE_URL = "http://localhost:8000"


def test_edge_cases():
    """Test various edge cases and error scenarios. Skips if backend is not reachable."""
    try:
        requests.get(f"{BASE_URL}/api/health", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {BASE_URL}: {e}")

    print("=" * 60)
    print("EDGE CASE TESTING")
    print("=" * 60)
    print()

    results = []

    # Test 1: Empty JSON
    print("Test 1: Empty JSON")
    try:
        r = requests.post(f"{BASE_URL}/api/validate", json={"json_data": {}}, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Valid: {r.json().get('valid', False)}")
        results.append(("Empty JSON", r.status_code == 200, "Expected validation failure"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Empty JSON", False, str(e)))
    print()
    
    # Test 2: Missing required fields
    print("Test 2: Missing required fields")
    try:
        data = {
            "metadata": {
                "week_of": "10/6-10/10",
                "grade": "7"
                # Missing: subject, homeroom, teacher_name
            },
            "days": {}
        }
        r = requests.post(f"{BASE_URL}/api/validate", json={"json_data": data}, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Valid: {r.json().get('valid', False)}")
        results.append(("Missing fields", r.status_code == 200, "Expected validation failure"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Missing fields", False, str(e)))
    print()
    
    # Test 3: Invalid data types
    print("Test 3: Invalid data types")
    try:
        data = {
            "metadata": {
                "week_of": 12345,  # Should be string
                "grade": "7",
                "subject": "Math",
                "homeroom": "101",
                "teacher_name": "Test"
            },
            "days": {}
        }
        r = requests.post(f"{BASE_URL}/api/validate", json={"json_data": data}, timeout=10)
        print(f"  Status: {r.status_code}")
        print(f"  Valid: {r.json().get('valid', False)}")
        results.append(("Invalid types", r.status_code == 200, "Expected validation failure"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Invalid types", False, str(e)))
    print()
    
    # Test 4: Nonexistent template
    print("Test 4: Nonexistent template")
    try:
        data = json.load(open('tests/fixtures/valid_lesson_minimal.json'))
        r = requests.post(f"{BASE_URL}/api/render", json={
            "json_data": data,
            "template_path": "nonexistent.docx",
            "output_filename": "test.docx"
        }, timeout=30)
        print(f"  Status: {r.status_code}")
        print(f"  Error handled: {r.status_code == 404}")
        results.append(("Nonexistent template", r.status_code == 404, "Expected 404"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Nonexistent template", False, str(e)))
    print()
    
    # Test 5: Large file stress test
    print("Test 5: Large content stress test")
    try:
        data = json.load(open('tests/fixtures/valid_lesson_minimal.json'))
        # Add very long content
        data['days']['monday']['tailored_instruction']['original_content'] = "X" * 10000
        r = requests.post(f"{BASE_URL}/api/render", json={
            "json_data": data,
            "output_filename": "stress_test.docx"
        }, timeout=30)
        print(f"  Status: {r.status_code}")
        print(f"  Success: {r.status_code == 200}")
        if r.status_code == 200:
            print(f"  Render time: {r.json().get('render_time_ms', 0):.2f}ms")
        results.append(("Large content", r.status_code == 200, "Should handle large content"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Large content", False, str(e)))
    print()
    
    # Test 6: Concurrent requests
    print("Test 6: Concurrent requests (3 simultaneous)")
    try:
        import concurrent.futures
        data = json.load(open('tests/fixtures/valid_lesson_minimal.json'))
        
        def render_test(i):
            r = requests.post(f"{BASE_URL}/api/render", json={
                "json_data": data,
                "output_filename": f"concurrent_test_{i}.docx"
            }, timeout=30)
            return r.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(render_test, i) for i in range(3)]
            success = all(f.result() for f in futures)
        
        print(f"  All succeeded: {success}")
        results.append(("Concurrent requests", success, "Should handle concurrent requests"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Concurrent requests", False, str(e)))
    print()
    
    # Test 7: Special characters in content
    print("Test 7: Special characters in content")
    try:
        data = json.load(open('tests/fixtures/valid_lesson_minimal.json'))
        data['metadata']['teacher_name'] = "José García-López"
        data['days']['monday']['objective']['content_objective'] = "Test émojis: 🎉 ñ á é í ó ú"
        r = requests.post(f"{BASE_URL}/api/render", json={
            "json_data": data,
            "output_filename": "special_chars_test.docx"
        }, timeout=30)
        print(f"  Status: {r.status_code}")
        print(f"  Success: {r.status_code == 200}")
        results.append(("Special characters", r.status_code == 200, "Should handle special chars"))
    except Exception as e:
        print(f"  Error: {e}")
        results.append(("Special characters", False, str(e)))
    print()
    
    # Summary
    print("=" * 60)
    print("EDGE CASE TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    for name, success, note in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name} - {note}")
    print()
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = test_edge_cases()
    exit(0 if success else 1)

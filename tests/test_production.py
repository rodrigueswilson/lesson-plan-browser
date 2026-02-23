"""Production deployment test script. Skips when backend is not running at localhost:8000."""
import json
from pathlib import Path

import pytest
import requests

def test_production_deployment():
    """Test production deployment with real data. Skips if backend is not reachable."""
    # Skip when backend is not running so full suite can complete without hanging
    try:
        r = requests.get("http://localhost:8000/api/health", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at localhost:8000: {e}")

    print("=" * 60)
    print("Production Deployment Test")
    print("=" * 60)

    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        r = requests.get("http://localhost:8000/api/health", timeout=5)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.json()}")
        assert r.status_code == 200
        print("   ✓ Health check passed")
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return False
    
    # Test 2: Validate JSON
    print("\n2. Testing JSON Validation...")
    try:
        with open("tests/fixtures/valid_lesson_minimal.json") as f:
            data = json.load(f)
        
        r = requests.post("http://localhost:8000/api/validate", json={"json_data": data}, timeout=10)
        print(f"   Status: {r.status_code}")
        result = r.json()
        print(f"   Valid: {result.get('valid')}")
        assert r.status_code == 200
        assert result.get("valid") == True
        print("   ✓ Validation passed")
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return False
    
    # Test 3: Render DOCX
    print("\n3. Testing DOCX Rendering...")
    try:
        r = requests.post("http://localhost:8000/api/render", json={"json_data": data}, timeout=30)
        print(f"   Status: {r.status_code}")
        result = r.json()
        output_path = result.get("output_path")
        print(f"   Output path: {output_path}")
        
        # Verify file exists
        if output_path:
            filepath = Path(output_path)
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"   File size: {size:,} bytes")
                print(f"   Render time: {result.get('render_time_ms', 0):.2f}ms")
                print("   ✓ Rendering passed")
                # Extract filename for download test
                filename = filepath.name
            else:
                print(f"   ✗ File not found: {filepath}")
                return False
        else:
            print(f"   ✗ No output_path in response: {result}")
            return False
    except Exception as e:
        print(f"   ✗ Rendering failed: {e}")
        return False
    
    # Test 4: Download File
    print("\n4. Testing File Download...")
    try:
        r = requests.get(f"http://localhost:8000/api/render/{filename}", timeout=10)
        print(f"   Status: {r.status_code}")
        print(f"   Content-Type: {r.headers.get('content-type')}")
        print(f"   Content-Length: {len(r.content):,} bytes")
        assert r.status_code == 200
        assert len(r.content) > 0
        print("   ✓ Download passed")
    except Exception as e:
        print(f"   ✗ Download failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL PRODUCTION TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_production_deployment()
    exit(0 if success else 1)

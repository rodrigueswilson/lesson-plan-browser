"""
Test the new training examples. Skips when backend not running at localhost:8000.
"""

import json
from pathlib import Path

import pytest
import requests

API_BASE = "http://localhost:8000"

def test_example(filepath):
    """Test validation and rendering of an example file. Skips if backend unreachable."""
    try:
        requests.get(f"{API_BASE}/api/health", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {API_BASE}: {e}")

    print(f"\n{'='*60}")
    print(f"Testing: {filepath.name}")
    print('='*60)

    # Load the file
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate
    print("\n1. Validating...")
    try:
        response = requests.post(
            f"{API_BASE}/api/validate",
            json={"json_data": data},
            timeout=10
        )
        result = response.json()
        
        if result.get('valid'):
            print("   ✅ Validation PASSED")
        else:
            print("   ❌ Validation FAILED")
            print(f"   Errors: {result.get('errors', [])}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Render
    print("\n2. Rendering...")
    try:
        output_name = f"training_{filepath.stem}.docx"
        response = requests.post(
            f"{API_BASE}/api/render",
            json={"json_data": data, "output_filename": output_name},
            timeout=30
        )
        result = response.json()
        
        if result.get('success'):
            print(f"   ✅ Rendering PASSED")
            print(f"   Output: {result.get('output_path')}")
            print(f"   Size: {result.get('file_size'):,} bytes")
            print(f"   Time: {result.get('render_time_ms'):.2f}ms")
            return True
        else:
            print(f"   ❌ Rendering FAILED")
            print(f"   Error: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("TESTING NEW TRAINING EXAMPLES")
    print("="*60)
    
    # Test health
    print("\nChecking system health...")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ System is healthy")
        else:
            print("❌ System health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test examples
    examples = [
        Path("tests/fixtures/training_example_simple.json"),
        Path("tests/fixtures/training_example_bilingual.json")
    ]
    
    results = []
    for example in examples:
        if example.exists():
            success = test_example(example)
            results.append((example.name, success))
        else:
            print(f"\n⚠️  File not found: {example}")
            results.append((example.name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All training examples are ready!")
    else:
        print("\n⚠️  Some examples need attention")

if __name__ == "__main__":
    main()

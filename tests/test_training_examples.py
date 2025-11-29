"""
Test script for training examples
Validates all example JSON files used in training
"""

import json
import requests
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_health():
    """Test system health"""
    print("\n=== Testing System Health ===")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_validate_file(filepath):
    """Test validation of a JSON file"""
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
        print(f"Valid: {result.get('valid', False)}")
        
        if not result.get('valid', False):
            print(f"Errors: {result.get('errors', [])}")
            print(f"Warnings: {result.get('warnings', [])}")
        
        return result.get('valid', False)
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_render_file(filepath):
    """Test rendering a JSON file to DOCX"""
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
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"Output: {result.get('output_path')}")
            print(f"Size: {result.get('file_size')} bytes")
            print(f"Time: {result.get('render_time_ms')}ms")
        else:
            print(f"Error: {result.get('error')}")
        
        return result.get('success', False)
    except Exception as e:
        print(f"ERROR: {e}")
        return False

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

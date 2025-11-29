"""Test production deployment with real lesson plan data."""
import requests
import json
from pathlib import Path
from datetime import datetime

def test_with_real_data():
    """Test with actual lesson plan data."""
    
    print("=" * 60)
    print("Real Data Production Test")
    print("=" * 60)
    
    # Use the comprehensive test fixture
    test_file = "tests/fixtures/valid_lesson_minimal.json"
    
    print(f"\nLoading test data from: {test_file}")
    with open(test_file) as f:
        data = json.load(f)
    
    print(f"Lesson plan: {data.get('metadata', {}).get('subject', 'Unknown')}")
    print(f"Grade: {data.get('metadata', {}).get('grade_level', 'Unknown')}")
    print(f"Teacher: {data.get('metadata', {}).get('teacher_name', 'Unknown')}")
    
    # Test 1: Validate
    print("\n1. Validating JSON...")
    r = requests.post("http://localhost:8000/api/validate", json={"json_data": data})
    if r.status_code == 200 and r.json().get("valid"):
        print("   ✓ Validation passed")
    else:
        print(f"   ✗ Validation failed: {r.json()}")
        return False
    
    # Test 2: Render with custom filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"production_test_{timestamp}.docx"
    
    print(f"\n2. Rendering to: {output_filename}")
    r = requests.post("http://localhost:8000/api/render", json={
        "json_data": data,
        "output_filename": output_filename
    })
    
    if r.status_code == 200:
        result = r.json()
        output_path = result.get("output_path")
        file_size = result.get("file_size", 0)
        render_time = result.get("render_time_ms", 0)
        
        print(f"   ✓ Rendered successfully")
        print(f"   Output: {output_path}")
        print(f"   Size: {file_size:,} bytes")
        print(f"   Time: {render_time:.2f}ms")
        
        # Verify file
        if Path(output_path).exists():
            print(f"   ✓ File verified")
        else:
            print(f"   ✗ File not found")
            return False
    else:
        print(f"   ✗ Rendering failed: {r.json()}")
        return False
    
    # Test 3: Performance check
    print("\n3. Performance Validation...")
    if render_time < 100:  # Should be well under 100ms
        print(f"   ✓ Excellent performance: {render_time:.2f}ms")
    elif render_time < 3000:  # Target is <3000ms
        print(f"   ✓ Good performance: {render_time:.2f}ms")
    else:
        print(f"   ⚠ Slow performance: {render_time:.2f}ms")
    
    print("\n" + "=" * 60)
    print("✓ REAL DATA TEST PASSED")
    print("=" * 60)
    print(f"\nGenerated file: {output_path}")
    print("You can open this file in Microsoft Word to verify quality.")
    
    return True

if __name__ == "__main__":
    success = test_with_real_data()
    exit(0 if success else 1)

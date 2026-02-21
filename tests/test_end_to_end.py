"""
End-to-End Integration Tests for Bilingual Lesson Plan Builder.

Tests the complete workflow from JSON input to DOCX output,
integrating all phases (0-6).

Test Scenarios:
1. Complete workflow: Validate → Render → Download
2. Error handling: Invalid JSON, missing template
3. Performance: Response times, file sizes
4. Integration: All components working together
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.validate_schema import validate_json, load_schema
from tools.docx_renderer import DOCXRenderer


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @staticmethod
    def load_fixture(filename: str) -> dict:
        """Load test fixture."""
        with open(f"tests/fixtures/{filename}", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def test_complete_workflow(self, client):
        """Test complete workflow: validate → render → download."""
        print("\n" + "="*60)
        print("Test: Complete Workflow")
        print("="*60)
        
        # Load valid lesson plan
        lesson_data = self.load_fixture("valid_lesson_minimal.json")
        
        # Step 1: Validate JSON
        print("\n1. Validating JSON...")
        start_time = time.time()
        response = client.post("/api/validate", json={"json_data": lesson_data})
        validate_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, "Validation should succeed"
        result = response.json()
        assert result["valid"] is True, "JSON should be valid"
        print(f"   ✓ Validation passed ({validate_time:.2f}ms)")
        
        # Step 2: Render to DOCX
        print("\n2. Rendering to DOCX...")
        start_time = time.time()
        response = client.post("/api/render", json={
            "json_data": lesson_data,
            "output_filename": "e2e_test_complete.docx"
        })
        render_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, "Rendering should succeed"
        result = response.json()
        assert result["success"] is True, "Rendering should succeed"
        assert result["output_path"] is not None, "Should have output path"
        assert result["file_size"] > 0, "File should have content"
        print(f"   ✓ Rendering completed ({render_time:.2f}ms)")
        print(f"   ✓ File size: {result['file_size']:,} bytes")
        
        # Step 3: Download file
        print("\n3. Downloading file...")
        filename = Path(result["output_path"]).name
        start_time = time.time()
        response = client.get(f"/api/render/{filename}")
        download_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, "Download should succeed"
        assert len(response.content) > 0, "Downloaded file should have content"
        assert len(response.content) == result["file_size"], "File sizes should match"
        print(f"   ✓ Download completed ({download_time:.2f}ms)")
        
        # Total time
        total_time = validate_time + render_time + download_time
        print(f"\n✓ COMPLETE WORKFLOW PASSED")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  - Validation: {validate_time:.2f}ms")
        print(f"  - Rendering: {render_time:.2f}ms")
        print(f"  - Download: {download_time:.2f}ms")
        
        return True
    
    def test_error_handling_workflow(self, client):
        """Test error handling throughout workflow."""
        print("\n" + "="*60)
        print("Test: Error Handling Workflow")
        print("="*60)
        
        # Test 1: Invalid JSON
        print("\n1. Testing invalid JSON...")
        invalid_json = {"metadata": {}, "days": {}}
        response = client.post("/api/validate", json={"json_data": invalid_json})
        
        assert response.status_code == 200, "Should return validation response"
        result = response.json()
        assert result["valid"] is False, "Should be invalid"
        assert len(result["errors"]) > 0, "Should have errors"
        print(f"   ✓ Invalid JSON detected ({len(result['errors'])} errors)")
        
        # Test 2: Render with invalid JSON
        print("\n2. Testing render with invalid JSON...")
        response = client.post("/api/render", json={
            "json_data": invalid_json,
            "output_filename": "should_fail.docx"
        })
        
        assert response.status_code == 400, "Should return 400 for invalid JSON"
        print("   ✓ Render rejected invalid JSON")
        
        # Test 3: Missing template
        print("\n3. Testing missing template...")
        valid_json = self.load_fixture("valid_lesson_minimal.json")
        response = client.post("/api/render", json={
            "json_data": valid_json,
            "output_filename": "test.docx",
            "template_path": "nonexistent/template.docx"
        })
        
        assert response.status_code == 404, "Should return 404 for missing template"
        print("   ✓ Missing template detected")
        
        # Test 4: Download nonexistent file
        print("\n4. Testing download nonexistent file...")
        response = client.get("/api/render/nonexistent_file.docx")
        
        assert response.status_code == 404, "Should return 404 for missing file"
        print("   ✓ Nonexistent file detected")
        
        print(f"\n✓ ERROR HANDLING PASSED")
        return True
    
    def test_performance_benchmarks(self, client):
        """Test performance benchmarks."""
        print("\n" + "="*60)
        print("Test: Performance Benchmarks")
        print("="*60)
        
        lesson_data = self.load_fixture("valid_lesson_minimal.json")
        
        # Benchmark validation
        print("\n1. Benchmarking validation (10 runs)...")
        times = []
        for i in range(10):
            start = time.time()
            response = client.post("/api/validate", json={"json_data": lesson_data})
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Min: {min_time:.2f}ms")
        print(f"   Max: {max_time:.2f}ms")
        print(f"   P95: {p95_time:.2f}ms")
        assert p95_time < 100, "P95 should be under 100ms"
        print("   ✓ Validation performance acceptable")
        
        # Benchmark rendering
        print("\n2. Benchmarking rendering (5 runs)...")
        times = []
        for i in range(5):
            start = time.time()
            response = client.post("/api/render", json={
                "json_data": lesson_data,
                "output_filename": f"perf_test_{i}.docx"
            })
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        print(f"   Average: {avg_time:.2f}ms")
        print(f"   Min: {min_time:.2f}ms")
        print(f"   Max: {max_time:.2f}ms")
        print(f"   P95: {p95_time:.2f}ms")
        assert p95_time < 3000, "P95 should be under 3s (target)"
        print("   ✓ Rendering performance acceptable")
        
        print(f"\n✓ PERFORMANCE BENCHMARKS PASSED")
        return True
    
    def test_component_integration(self, client):
        """Test integration of all components."""
        print("\n" + "="*60)
        print("Test: Component Integration")
        print("="*60)
        
        # Test Phase 1: Schema validation
        print("\n1. Testing Phase 1 (Schema Validation)...")
        schema = load_schema(Path("schemas/lesson_output_schema.json"))
        lesson_data = self.load_fixture("valid_lesson_minimal.json")
        is_valid, errors = validate_json(lesson_data, schema)
        assert is_valid, "Direct schema validation should work"
        print("   ✓ Phase 1 integration working")
        
        # Test Phase 5: DOCX rendering
        print("\n2. Testing Phase 5 (DOCX Renderer)...")
        renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")
        output_path = "output/integration_test.docx"
        success = renderer.render(lesson_data, output_path)
        assert success, "Direct DOCX rendering should work"
        assert Path(output_path).exists(), "Output file should exist"
        print("   ✓ Phase 5 integration working")
        
        # Test Phase 6: API integration
        print("\n3. Testing Phase 6 (FastAPI)...")
        response = client.get("/api/health")
        assert response.status_code == 200, "API should be healthy"
        print("   ✓ Phase 6 integration working")
        
        # Test all phases together via API
        print("\n4. Testing all phases via API...")
        response = client.post("/api/render", json={
            "json_data": lesson_data,
            "output_filename": "full_integration_test.docx"
        })
        assert response.status_code == 200, "Full integration should work"
        result = response.json()
        assert result["success"] is True, "Full integration should succeed"
        print("   ✓ Full integration working")
        
        print(f"\n✓ COMPONENT INTEGRATION PASSED")
        return True
    
    def test_data_integrity(self, client):
        """Test data integrity through the pipeline."""
        print("\n" + "="*60)
        print("Test: Data Integrity")
        print("="*60)
        
        lesson_data = self.load_fixture("valid_lesson_minimal.json")
        
        # Render via API
        print("\n1. Rendering lesson plan...")
        response = client.post("/api/render", json={
            "json_data": lesson_data,
            "output_filename": "integrity_test.docx"
        })
        
        assert response.status_code == 200, "Rendering should succeed"
        result = response.json()
        
        # Verify file exists and has content
        print("\n2. Verifying file integrity...")
        output_path = Path(result["output_path"])
        assert output_path.exists(), "Output file should exist"
        assert output_path.stat().st_size > 0, "File should have content"
        assert output_path.stat().st_size == result["file_size"], "File sizes should match"
        print(f"   ✓ File exists: {output_path}")
        print(f"   ✓ File size: {result['file_size']:,} bytes")
        
        # Verify metadata
        print("\n3. Verifying metadata...")
        assert "week_of" in lesson_data["metadata"], "Should have week_of"
        assert "grade" in lesson_data["metadata"], "Should have grade"
        assert "subject" in lesson_data["metadata"], "Should have subject"
        print("   ✓ Metadata intact")
        
        # Verify all days present
        print("\n4. Verifying all days...")
        required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for day in required_days:
            assert day in lesson_data["days"], f"Should have {day}"
        print("   ✓ All days present")
        
        print(f"\n✓ DATA INTEGRITY PASSED")
        return True


def run_all_tests():
    """Run all end-to-end tests."""
    print("\n" + "="*60)
    print("END-TO-END INTEGRATION TESTS")
    print("="*60)
    print("\nTesting complete workflow from JSON to DOCX")
    print("Integrating Phases 0-6")
    print("="*60)
    
    test_suite = TestEndToEnd()
    
    tests = [
        ("Complete Workflow", test_suite.test_complete_workflow),
        ("Error Handling", test_suite.test_error_handling_workflow),
        ("Performance Benchmarks", test_suite.test_performance_benchmarks),
        ("Component Integration", test_suite.test_component_integration),
        ("Data Integrity", test_suite.test_data_integrity),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("END-TO-END TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL END-TO-END TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

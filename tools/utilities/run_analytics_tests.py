"""
Test runner for analytics tests.
Runs all analytics-related tests and generates a report.
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all analytics tests."""
    print("=" * 70)
    print("ANALYTICS DASHBOARD TEST SUITE")
    print("=" * 70)
    print()
    
    test_files = [
        ("Unit Tests", "tests/test_analytics_endpoints.py"),
        ("Integration Tests", "tests/test_analytics_integration.py"),
    ]
    
    results = {}
    
    for test_name, test_file in test_files:
        print(f"\n{'=' * 70}")
        print(f"Running: {test_name}")
        print(f"File: {test_file}")
        print("=" * 70)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            results[test_name] = {
                "passed": result.returncode == 0,
                "output": result.stdout
            }
            
        except subprocess.TimeoutExpired:
            print(f"ERROR: {test_name} timed out after 60 seconds")
            results[test_name] = {"passed": False, "output": "Timeout"}
        except Exception as e:
            print(f"ERROR running {test_name}: {e}")
            results[test_name] = {"passed": False, "output": str(e)}
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["passed"])
    
    for test_name, result in results.items():
        status = "PASSED" if result["passed"] else "FAILED"
        symbol = "✓" if result["passed"] else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print()
    print(f"Total: {passed_tests}/{total_tests} test suites passed")
    print("=" * 70)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

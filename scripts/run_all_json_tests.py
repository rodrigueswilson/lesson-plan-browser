
import subprocess
import sys
import os

def run_test(name, command):
    print(f"\n{'='*20} RUNNING TEST: {name} {'='*20}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        print(f"SUCCESS: {name} passed.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(f"ERROR: {name} failed with exit code {e.returncode}")
        print(e.stderr)
        return False

def main():
    tests = [
        ("Reproduction Script", [sys.executable, "scripts/reproduce_wida_error.py"]),
        ("JSON Repair Lib Check", [sys.executable, "scripts/test_json_repair_lib_v2.py"]),
        ("Resilience Suite", [sys.executable, "tests/test_json_resilience.py"]),
        ("Instructor Integration (Mocked)", [sys.executable, "scripts/test_instructor_full.py"]),
    ]
    
    all_passed = True
    for name, cmd in tests:
        if not run_test(name, cmd):
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED. CHECK LOGS ABOVE.")
    print("="*50)

if __name__ == "__main__":
    main()

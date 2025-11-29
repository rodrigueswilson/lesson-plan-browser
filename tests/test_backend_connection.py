"""Test if backend is accessible."""
import requests
import sys

try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"✓ Backend is accessible!")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    sys.exit(0)
except requests.exceptions.ConnectionError as e:
    print(f"✗ Cannot connect to backend!")
    print(f"Error: {e}")
    print("\nBackend is NOT running or not accessible on port 8000")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

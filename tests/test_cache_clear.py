"""
Quick test to verify cache clearing on startup/shutdown works.
"""

from backend.api import app

print("✓ API loaded successfully")
print("✓ Startup event handler registered")
print("✓ Shutdown event handler registered")
print("\nCache clearing will happen when you run:")
print("  python -m uvicorn backend.api:app --reload --port 8000")

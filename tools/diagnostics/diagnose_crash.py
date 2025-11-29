"""
Diagnostic script to identify backend crash causes.
Run this before starting the full app to catch initialization errors.
"""

import sys
from pathlib import Path

print("=" * 60)
print("BACKEND CRASH DIAGNOSTIC")
print("=" * 60)
print()

# Test 1: Python environment
print("[1/8] Checking Python version...")
print(f"  Python: {sys.version}")
print(f"  Executable: {sys.executable}")
print()

# Test 2: Critical imports
print("[2/8] Testing critical imports...")
try:
    import fastapi
    print(f"  FastAPI: {fastapi.__version__}")
except Exception as e:
    print(f"  ERROR importing FastAPI: {e}")
    sys.exit(1)

try:
    import uvicorn
    print(f"  Uvicorn: {uvicorn.__version__}")
except Exception as e:
    print(f"  ERROR importing Uvicorn: {e}")
    sys.exit(1)

try:
    from docx import Document
    print(f"  python-docx: OK")
except Exception as e:
    print(f"  ERROR importing python-docx: {e}")
    sys.exit(1)

print()

# Test 3: Backend module imports
print("[3/8] Testing backend module imports...")
try:
    from backend.config import settings
    print(f"  backend.config: OK")
    print(f"    DATABASE_URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"  ERROR importing backend.config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from backend.database import Database
    print(f"  backend.database: OK")
except Exception as e:
    print(f"  ERROR importing backend.database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from backend.llm_service import get_llm_service
    print(f"  backend.llm_service: OK")
except Exception as e:
    print(f"  ERROR importing backend.llm_service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Database initialization
print("[4/8] Testing database initialization...")
try:
    db = Database()
    print(f"  Database path: {db.db_path}")
    print(f"  Database exists: {db.db_path.exists()}")
    
    # Try a simple query
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"  User count: {count}")
except Exception as e:
    print(f"  ERROR initializing database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Template file check
print("[5/8] Checking template file...")
template_path = Path(settings.DOCX_TEMPLATE_PATH)
if template_path.exists():
    print(f"  Template found: {template_path}")
    print(f"  Size: {template_path.stat().st_size} bytes")
else:
    print(f"  WARNING: Template not found at {template_path}")
print()

# Test 6: API module import
print("[6/8] Testing API module import...")
try:
    from backend.api import app
    print(f"  backend.api: OK")
    print(f"  App title: {app.title}")
except Exception as e:
    print(f"  ERROR importing backend.api: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 7: Batch processor import
print("[7/8] Testing batch processor import...")
try:
    from tools.batch_processor import BatchProcessor
    print(f"  tools.batch_processor: OK")
except Exception as e:
    print(f"  ERROR importing batch_processor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 8: DOCX tools import
print("[8/8] Testing DOCX tools import...")
try:
    from tools.docx_parser import DOCXParser
    print(f"  tools.docx_parser: OK")
except Exception as e:
    print(f"  ERROR importing docx_parser: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from tools.docx_renderer import DOCXRenderer
    print(f"  tools.docx_renderer: OK")
except Exception as e:
    print(f"  ERROR importing docx_renderer: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("ALL DIAGNOSTICS PASSED!")
print("=" * 60)
print()
print("Next steps:")
print("1. Run: python -m uvicorn backend.api:app --reload --port 8000")
print("2. Keep terminal visible")
print("3. Process a lesson plan from the frontend")
print("4. Share any error messages that appear")
print()

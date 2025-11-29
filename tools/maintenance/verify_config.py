"""
Quick configuration verification script.
Checks for common configuration issues that cause crashes.
"""

import os
from pathlib import Path

print("=" * 60)
print("CONFIGURATION VERIFICATION")
print("=" * 60)
print()

# Check 1: .env file exists
print("[1/6] Checking .env file...")
env_path = Path(".env")
if env_path.exists():
    print(f"  .env found: {env_path.absolute()}")
    print(f"  Size: {env_path.stat().st_size} bytes")
else:
    print("  WARNING: .env file not found!")
    print("  Copy .env.example to .env and configure it")
print()

# Check 2: Load settings
print("[2/6] Loading settings...")
try:
    from backend.config import settings
    print(f"  Settings loaded successfully")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
    print(f"  LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"  LLM_MODEL: {settings.LLM_MODEL}")
    print(f"  DOCX_TEMPLATE_PATH: {settings.DOCX_TEMPLATE_PATH}")
except Exception as e:
    print(f"  ERROR loading settings: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
print()

# Check 3: Database path
print("[3/6] Checking database path...")
db_url = settings.DATABASE_URL
db_path_str = db_url.replace("sqlite:///", "").replace("sqlite://", "")
db_path = Path(db_path_str)
print(f"  Parsed path: {db_path.absolute()}")
print(f"  Database exists: {db_path.exists()}")
print(f"  Parent directory exists: {db_path.parent.exists()}")

if not db_path.parent.exists():
    print(f"  Creating parent directory: {db_path.parent}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
print()

# Check 4: Template file
print("[4/6] Checking template file...")
template_path = Path(settings.DOCX_TEMPLATE_PATH)
print(f"  Template path: {template_path.absolute()}")
if template_path.exists():
    print(f"  Template found: {template_path.stat().st_size} bytes")
else:
    print(f"  ERROR: Template not found!")
    print(f"  Expected at: {template_path.absolute()}")
print()

# Check 5: API key
print("[5/6] Checking API key...")
if settings.LLM_API_KEY:
    key_preview = settings.LLM_API_KEY[:10] + "..." if len(settings.LLM_API_KEY) > 10 else "***"
    print(f"  LLM_API_KEY: {key_preview} (length: {len(settings.LLM_API_KEY)})")
else:
    print("  WARNING: LLM_API_KEY not set")
    print("  Set LLM_API_KEY in .env file")
print()

# Check 6: Critical directories
print("[6/6] Checking critical directories...")
dirs_to_check = [
    "backend",
    "tools",
    "input",
    "output",
    "schemas",
    "data",
]

for dir_name in dirs_to_check:
    dir_path = Path(dir_name)
    exists = dir_path.exists()
    status = "OK" if exists else "MISSING"
    print(f"  {dir_name}/: {status}")
    if not exists and dir_name in ["output", "data"]:
        print(f"    Creating {dir_name}/...")
        dir_path.mkdir(parents=True, exist_ok=True)

print()
print("=" * 60)
print("CONFIGURATION CHECK COMPLETE")
print("=" * 60)
print()

# Summary
issues = []
if not env_path.exists():
    issues.append("Missing .env file")
if not template_path.exists():
    issues.append("Missing template file")
if not settings.LLM_API_KEY:
    issues.append("Missing API key")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  - {issue}")
    print()
    print("Fix these issues before starting the backend.")
else:
    print("All checks passed! Ready to start backend.")
    print()
    print("Next: Run 'python diagnose_crash.py' for deeper diagnostics")
print()

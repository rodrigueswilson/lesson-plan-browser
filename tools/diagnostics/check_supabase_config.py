"""
Check Supabase configuration and test connectivity.

This script helps verify that your Supabase setup is correct before running tests.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("[ERROR] .env file not found!")
        print("\nPlease create a .env file in the project root with:")
        print("""
USE_SUPABASE=True
SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
SUPABASE_KEY_PROJECT1=your-project1-anon-key
SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
SUPABASE_KEY_PROJECT2=your-project2-anon-key
        """)
        return False
    
    print("[OK] .env file found")
    return True

def check_env_variables():
    """Check if required environment variables are set."""
    from backend.config import Settings
    
    settings = Settings()
    
    issues = []
    
    if not settings.USE_SUPABASE:
        issues.append("USE_SUPABASE is not set to True")
    
    if not settings.SUPABASE_URL_PROJECT1:
        issues.append("SUPABASE_URL_PROJECT1 is not set")
    
    if not settings.SUPABASE_KEY_PROJECT1:
        issues.append("SUPABASE_KEY_PROJECT1 is not set")
    
    if not settings.SUPABASE_URL_PROJECT2:
        issues.append("SUPABASE_URL_PROJECT2 is not set")
    
    if not settings.SUPABASE_KEY_PROJECT2:
        issues.append("SUPABASE_KEY_PROJECT2 is not set")
    
    if issues:
        print("\n[ERROR] Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("[OK] All required environment variables are set")
    return True

def test_supabase_connection():
    """Test connection to both Supabase projects."""
    from backend.config import Settings
    from supabase import create_client
    
    settings = Settings()
    
    print("\nTesting Supabase connections...")
    
    # Test Project 1
    print("\n[Project 1 - Wilson]")
    try:
        client1 = create_client(settings.SUPABASE_URL_PROJECT1, settings.SUPABASE_KEY_PROJECT1)
        # Try to query users table
        response = client1.table("users").select("id").limit(1).execute()
        print("[OK] Connected successfully")
        print("[OK] Schema verified (users table exists)")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    
    # Test Project 2
    print("\n[Project 2 - Daniela]")
    try:
        client2 = create_client(settings.SUPABASE_URL_PROJECT2, settings.SUPABASE_KEY_PROJECT2)
        # Try to query users table
        response = client2.table("users").select("id").limit(1).execute()
        print("[OK] Connected successfully")
        print("[OK] Schema verified (users table exists)")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    
    return True

def check_users():
    """Check if test users exist in Supabase."""
    from backend.database import get_db
    
    print("\nChecking for test users...")
    
    try:
        db = get_db()
        users = db.list_users()
        
        wilson = None
        daniela = None
        
        for user in users:
            name = user.get('name', '') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            if 'wilson' in name.lower():
                wilson = user
            if 'daniela' in name.lower():
                daniela = user
        
        if wilson:
            print(f"[OK] Found Wilson: {wilson.get('id')}")
        else:
            print("[WARN] Wilson not found (will be created during test)")
        
        if daniela:
            print(f"[OK] Found Daniela: {daniela.get('id')}")
        else:
            print("[WARN] Daniela not found (will be created during test)")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error checking users: {e}")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("Supabase Configuration Checker")
    print("=" * 60)
    
    checks = [
        ("Environment file", check_env_file),
        ("Environment variables", check_env_variables),
        ("Supabase connections", test_supabase_connection),
        ("Test users", check_users),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n[SUCCESS] All checks passed! You're ready to test with Supabase.")
        print("\nNext steps:")
        print("1. Restart the backend to load new settings")
        print("2. Run: python test_supabase_integration.py")
        return 0
    else:
        print("\n[WARN] Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


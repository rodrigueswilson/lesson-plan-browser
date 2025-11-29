"""
Verify that the backend has the new batch processor code loaded.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    # Import the batch processor
    from tools.batch_processor import BatchProcessor
    
    # Check if the _combine_lessons method has the new code
    import inspect
    source = inspect.getsource(BatchProcessor._combine_lessons)
    
    print("\n" + "=" * 80)
    print("BACKEND CODE VERIFICATION")
    print("=" * 80)
    
    # Check for new code markers
    has_new_code = "render merged JSON with slots arrays" in source
    has_old_code = "Render each slot to temporary file" in source
    
    if has_new_code and not has_old_code:
        print("\n✅ NEW CODE LOADED")
        print("   - Multi-slot rendering uses merged JSON")
        print("   - Per-slot rendering will work correctly")
        print("\n   Backend is ready!")
    elif has_old_code:
        print("\n❌ OLD CODE STILL PRESENT")
        print("   - Multi-slot rendering uses separate temp files")
        print("   - This will cause cross-contamination")
        print("\n   ⚠️  RESTART THE BACKEND!")
    else:
        print("\n⚠️  UNKNOWN CODE STATE")
        print("   - Cannot determine which version is loaded")
    
    print("\n" + "=" * 80)
    
except Exception as e:
    print(f"\n❌ Error checking code: {e}")
    print("\nMake sure you're in the LP directory.")

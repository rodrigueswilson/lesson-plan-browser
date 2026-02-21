"""Test enhanced warning messages with actual lesson plan generation."""

import asyncio
import io
import sys
from pathlib import Path

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.supabase_database import SupabaseDatabase
from tools.batch_processor import BatchProcessor


async def test_enhanced_warnings():
    """Test enhanced warnings by generating a lesson plan."""
    print("=" * 60)
    print("TESTING ENHANCED WARNING MESSAGES")
    print("=" * 60)

    # Initialize database
    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return False

    # Use Daniela Silva (we know she has mismatches)
    user_id = "29fa9ed7-3174-4999-86fd-40a542c28cff"
    week_of = "12/15-12/19"

    print(f"\nUser ID: {user_id}")
    print(f"Week: {week_of}")

    # Get user info
    user_info = db.client.table("users").select("*").eq("id", user_id).execute()
    if not user_info.data:
        print("ERROR: User not found")
        return False

    user_data = user_info.data[0]
    print(f"User: {user_data.get('name', 'N/A')}")
    print(f"Base path: {user_data.get('base_path_override', 'N/A')}")

    # Get slots
    slots = db.get_user_slots(user_id)
    print(f"\nSlots configured: {len(slots)}")
    for slot in sorted(slots, key=lambda x: x.slot_number):
        print(
            f"  Slot {slot.slot_number}: {slot.subject} ({slot.primary_teacher_name or 'N/A'})"
        )

    # Initialize processor
    print("\nInitializing batch processor...")
    processor = BatchProcessor()

    # Process one slot to test warnings (slot 4 has a mismatch)
    print("\n" + "=" * 60)
    print("PROCESSING SLOT 4 (Science, Morais)")
    print("=" * 60)
    print("This slot should trigger a multi-slot mismatch warning.")
    print("Expected: Slot 4 requested, but document has Science in slot 3")

    # Find slot 4
    slot_4 = next((s for s in slots if s.slot_number == 4), None)
    if not slot_4:
        print("ERROR: Slot 4 not found")
        return False

    # Convert slot to dict format
    slot_dict = {
        "slot_number": slot_4.slot_number,
        "subject": slot_4.subject,
        "grade": slot_4.grade,
        "homeroom": slot_4.homeroom,
        "primary_teacher_name": slot_4.primary_teacher_name,
        "primary_teacher_file_pattern": slot_4.primary_teacher_file_pattern,
        "primary_teacher_first_name": slot_4.primary_teacher_first_name,
        "primary_teacher_last_name": slot_4.primary_teacher_last_name,
    }

    try:
        # Process the slot
        print("\nProcessing slot...")
        result = await processor._process_slot(
            slot_dict,
            week_of,
            "openai",
            week_folder_path=None,  # Auto-detect
            user_base_path=user_data.get("base_path_override"),
            plan_id=None,
            slot_index=1,
            total_slots=1,
            processing_weight=1.0,
        )

        print("\n[SUCCESS] Slot processed successfully")
        print(
            f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
        )

        return True

    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def check_recent_logs():
    """Check recent log files for enhanced warnings."""
    print("\n" + "=" * 60)
    print("CHECKING RECENT LOGS FOR ENHANCED WARNINGS")
    print("=" * 60)

    log_dir = Path("logs")
    if not log_dir.exists():
        print("Logs directory not found")
        return

    # Find most recent backend log
    backend_logs = sorted(
        log_dir.glob("backend_*.log"), key=lambda x: x.stat().st_mtime, reverse=True
    )

    if not backend_logs:
        print("No backend logs found")
        return

    latest_log = backend_logs[0]
    print(f"\nChecking: {latest_log.name}")

    # Search for enhanced warnings
    with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Look for enhanced warning types
    warning_types = [
        "slot_subject_mismatch_single_slot",
        "slot_subject_mismatch_multi_slot",
        "slot_auto_mapped",
    ]

    found_warnings = []
    for i, line in enumerate(lines):
        for warning_type in warning_types:
            if warning_type in line:
                # Get context (5 lines before and after)
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                context = "".join(lines[start:end])
                found_warnings.append(
                    {
                        "type": warning_type,
                        "line": i + 1,
                        "context": context,
                    }
                )

    if found_warnings:
        print(f"\nFound {len(found_warnings)} enhanced warning(s):")
        for warning in found_warnings:
            print(f"\n{warning['type']} (line {warning['line']}):")
            print("-" * 60)
            print(warning["context"][:500])  # First 500 chars
    else:
        print("\nNo enhanced warnings found in recent logs")
        print("(This is expected if no processing has occurred since enhancement)")


if __name__ == "__main__":
    print("\nNote: This test requires the backend to be running.")
    print("The test will process a single slot to trigger warnings.")
    print("\nOptions:")
    print("1. Run async test (requires backend)")
    print("2. Check recent logs for warnings")
    print("3. Both")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1" or choice == "3":
        try:
            result = asyncio.run(test_enhanced_warnings())
            if result:
                print("\n[SUCCESS] Test completed")
            else:
                print("\n[FAILED] Test failed")
        except Exception as e:
            print(f"\n[ERROR] Test error: {e}")
            import traceback

            traceback.print_exc()

    if choice == "2" or choice == "3":
        check_recent_logs()

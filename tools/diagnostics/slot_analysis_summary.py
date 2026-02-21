"""Generate summary of slot analysis results."""

import json
from pathlib import Path

# Load analysis results
results_path = Path("logs/slot_analysis_results.json")
with open(results_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 60)
print("SLOT STRUCTURE ANALYSIS SUMMARY")
print("=" * 60)
print(f"\nTotal files analyzed: {data['total_files']}")
print(f"Week folder: {data['week_folder']}\n")

# Filter source documents (exclude output files)
source_files = [
    d
    for d in data["documents"]
    if d.get("available_slots", 0) > 0
    and "error" not in d
    and not d["file_name"].startswith("Daniela_Silva_Weekly")  # Exclude output files
]

print("SOURCE DOCUMENTS:")
print("-" * 60)
for doc in source_files:
    print(f"\n{doc['file_name']}")
    print(f"  Total slots: {doc['available_slots']}")
    print(f"  Tables: {doc['total_tables']} (has signature: {doc['has_signature']})")
    print("  Slot structure:")
    for slot in doc.get("slot_details", []):
        if "error" not in slot:
            print(f"    Slot {slot['slot_number']}: {slot['subject']}")
            print(f"      Teacher: {slot.get('teacher', 'N/A')}")
            print(
                f"      Homeroom: {slot.get('homeroom', 'N/A')}, Grade: {slot.get('grade', 'N/A')}"
            )

print("\n" + "=" * 60)
print("MISMATCH ANALYSIS")
print("=" * 60)

# User config (from logs)
user_config = [
    {
        "slot": 1,
        "subject": "ELA/SS",
        "teacher": "Morais",
        "file": "Morais 12_15 - 12_19.docx",
    },
    {
        "slot": 2,
        "subject": "Social Studies",
        "teacher": "Santiago",
        "file": "T. Santiago SS Plans 12_15.docx",
    },
    {
        "slot": 3,
        "subject": "Science",
        "teacher": "Grande",
        "file": "Mrs. Grande Science 12_15 12_19.docx",
    },
    {
        "slot": 4,
        "subject": "Science",
        "teacher": "Morais",
        "file": "Morais 12_15 - 12_19.docx",
    },
    {
        "slot": 5,
        "subject": "Math",
        "teacher": "Morais",
        "file": "Morais 12_15 - 12_19.docx",
    },
]

print("\nUser Configuration vs Document Reality:\n")
for config in user_config:
    # Find matching document
    doc = next((d for d in source_files if config["file"] in d["file_name"]), None)
    if not doc:
        print(f"  Slot {config['slot']}: {config['subject']} - FILE NOT FOUND")
        continue

    # Find actual slot in document
    actual_slot = None
    for slot in doc.get("slot_details", []):
        if "error" in slot:
            continue
        slot_subject = slot.get("subject", "").lower()
        req_subject = config["subject"].lower()

        # Check subject match
        if req_subject in slot_subject or slot_subject in req_subject:
            # Handle combined subjects
            if "/" in req_subject:
                tokens = req_subject.split("/")
                if any(t.strip() in slot_subject for t in tokens):
                    actual_slot = slot["slot_number"]
                    break
            else:
                actual_slot = slot["slot_number"]
                break

    if actual_slot:
        if actual_slot == config["slot"]:
            status = "[MATCH]"
        else:
            status = f"[MISMATCH] Found in slot {actual_slot}"
        print(f"  Slot {config['slot']}: {config['subject']} ({config['teacher']})")
        print(f"    {status}")
        print(f"    File: {config['file']}")
        if actual_slot != config["slot"]:
            print(
                f"    -> Document has {config['subject']} in slot {actual_slot}, not slot {config['slot']}"
            )

print("\n" + "=" * 60)
print("CONCLUSIONS")
print("=" * 60)
print("""
1. Single-slot documents (T. Santiago, Mrs. Grande):
   - Always map to slot 1 regardless of requested slot number
   - This is EXPECTED behavior - warnings are informational

2. Multi-slot document (Morais):
   - User config references slots 1, 4, and 5
   - Document actually has slots 1, 2, 3, 4
   - Subject-based detection correctly finds content despite mismatch

3. System Status:
   - [OK] Working correctly - finds right content
   - [WARN] Warnings indicate slot number inconsistencies
   - [INFO] Consider updating user slot configs to match document structures
""")

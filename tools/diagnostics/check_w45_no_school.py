"""
Script to check for "No School" days in W45 primary teacher lesson plans.
"""

from pathlib import Path
from tools.docx_parser import DOCXParser

# Path to W45 folder
w45_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W45")

# Teacher files
teacher_files = {
    "Morais": "Morais 11_3_25 - 11_7_25.docx",
    "Grande": "Mrs. Grande Science 11_03- 11_07.docx",
    "Santiago": "T. Santiago SS Plans 11_3-11_7.docx"
}

print("=" * 70)
print("Checking for 'No School' days in W45 lesson plans")
print("=" * 70)

for teacher_name, filename in teacher_files.items():
    file_path = w45_folder / filename
    
    if not file_path.exists():
        print(f"\n[ERROR] {teacher_name}: File not found: {filename}")
        continue
    
    print(f"\n{'='*70}")
    print(f"Teacher: {teacher_name}")
    print(f"File: {filename}")
    print(f"{'='*70}")
    
    try:
        parser = DOCXParser(str(file_path))
        
        # Get all slots/subjects in the document
        total_tables = len(parser.doc.tables)
        available_slots = (total_tables - 1) // 2  # Exclude signature table
        
        print(f"Found {available_slots} slot(s) in document")
        
        all_no_school_days = {}
        
        # Check each slot
        for slot_num in range(1, available_slots + 1):
            try:
                # Validate slot structure
                from tools.docx_parser import validate_slot_structure
                table_start, table_end = validate_slot_structure(parser.doc, slot_num)
                meta_table = parser.doc.tables[table_start]
                
                # Extract subject and teacher from metadata
                subject = None
                teacher = None
                for row in meta_table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        cell_lower = cell_text.lower()
                        if 'subject:' in cell_lower:
                            subject = cell_text.split(':', 1)[-1].strip()
                        if 'name:' in cell_lower or 'teacher:' in cell_lower:
                            teacher = cell_text.split(':', 1)[-1].strip()
                
                if not subject:
                    print(f"  Slot {slot_num}: [WARNING] Could not find subject")
                    continue
                
                print(f"\n  Slot {slot_num}: {subject}" + (f" ({teacher})" if teacher else ""))
                
                # Extract content for this slot
                content = parser.extract_subject_content_for_slot(slot_num, subject)
                
                # Get No School days
                no_school_days = content.get('no_school_days', [])
                
                if no_school_days:
                    print(f"    [FOUND] No School days detected: {', '.join(no_school_days)}")
                    all_no_school_days[subject] = no_school_days
                    
                    # Show the content that triggered detection
                    table_content = content.get('table_content', {})
                    for day in no_school_days:
                        if day in table_content:
                            day_content = table_content[day]
                            day_text = " ".join(day_content.values())
                            print(f"      {day}: {day_text[:100]}...")
                else:
                    print(f"    [OK] No 'No School' days detected")
                    
            except Exception as e:
                print(f"  Slot {slot_num}: [ERROR] {e}")
                continue
        
        # Summary
        if all_no_school_days:
            print(f"\n[SUMMARY] {teacher_name}:")
            for subject, days in all_no_school_days.items():
                print(f"  - {subject}: {', '.join(days)}")
        else:
            print(f"\n[SUMMARY] {teacher_name}: No 'No School' days detected")
            
    except Exception as e:
        print(f"\n[ERROR] Error processing {teacher_name}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Check complete")
print("=" * 70)


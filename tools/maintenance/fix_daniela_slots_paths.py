from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

# Define the file mappings based on W44 structure
file_mappings = {
    1: r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44\Lang Lesson Plans 10_27_25-10_31_25.docx",
    2: r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44\Lang Lesson Plans 10_27_25-10_31_25.docx",  # Social Studies might be in Lang file
    3: r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44\Ms. Savoca-10_27_25-10_31_25 Lesson plans.docx",
    4: r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44\Ms. Savoca-10_27_25-10_31_25 Lesson plans.docx",
    5: r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W44\Ms. Savoca-10_27_25-10_31_25 Lesson plans.docx"
}

print(f"Updating slots for {user['name']}...\n")

with db.get_connection() as conn:
    cursor = conn.cursor()
    
    for slot in slots:
        slot_num = slot['slot_number']
        file_path = file_mappings.get(slot_num)
        
        if file_path:
            cursor.execute("""
                UPDATE class_slots
                SET primary_teacher_file = ?
                WHERE id = ?
            """, (file_path, slot['id']))
            
            print(f"✅ Slot {slot_num} ({slot['subject']}): {file_path}")
    
    conn.commit()
    print(f"\n✅ All slots updated!")

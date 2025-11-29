from backend.database import Database

db = Database()

# Get Daniela's user
user = db.get_user_by_name('Daniela Silva')
slots = db.get_user_slots(user['id'])

# Find slot 5
slot5 = [s for s in slots if s['slot_number'] == 5][0]

print("=== Slot 5 Configuration ===")
print(f"Subject: {slot5['subject']}")
print(f"Teacher First Name: {slot5.get('primary_teacher_first_name')}")
print(f"Teacher Last Name: {slot5.get('primary_teacher_last_name')}")
print(f"Teacher File: {slot5.get('primary_teacher_file')}")
print(f"Teacher Name: {slot5.get('primary_teacher_name')}")

print("\n=== Available Files in W44 ===")
import os
folder = r"F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W44"
for f in os.listdir(folder):
    if f.endswith('.docx') and not f.startswith('~$'):
        print(f"  - {f}")

print("\n=== Expected Match ===")
print(f"Looking for file with 'Morais' in name for Math subject")
print(f"File 'Morais 10_27-31.docx' should match")

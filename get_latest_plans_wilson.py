
import sys
import os
sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

db = SQLiteDatabase()
plans = db.get_user_plans("04fe8898-cb89-4a73-affb-64a97a98f820", limit=5)
if not plans:
    print("No plans found for Wilson Rodrigues.")
for p in plans:
    print(f"Plan ID: {p.id}, Week: {p.week_of}, Status: {p.status}")

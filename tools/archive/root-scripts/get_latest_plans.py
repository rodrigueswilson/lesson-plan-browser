
import sys
import os
sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

db = SQLiteDatabase()
plans = db.get_user_plans("rodri", limit=5)
for p in plans:
    print(f"Plan ID: {p.id}, Week: {p.week_of}, Status: {p.status}")

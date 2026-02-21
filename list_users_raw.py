
import sys
import os
sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase
import sqlite3

conn = sqlite3.connect("data/lesson_plans.db")
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM users")
for row in cursor.fetchall():
    print(f"User ID: {row[0]}, Name: {row[1]}")
conn.close()

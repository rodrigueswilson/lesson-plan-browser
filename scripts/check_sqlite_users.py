#!/usr/bin/env python3
"""Check SQLite database for users."""
import sqlite3
import os
import json

db_path = './data/lesson_planner.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute('SELECT id, first_name, last_name, email, created_at FROM users')
        users = cursor.fetchall()
        print(f"SQLite users found: {len(users)}")
        print()
        for user in users:
            print(f"  ID: {user[0]}")
            print(f"  Name: {user[1]} {user[2]}")
            print(f"  Email: {user[3]}")
            print(f"  Created: {user[4]}")
            print()
    else:
        print("Users table does not exist in SQLite")
    
    conn.close()
else:
    print(f"SQLite database not found at {db_path}")


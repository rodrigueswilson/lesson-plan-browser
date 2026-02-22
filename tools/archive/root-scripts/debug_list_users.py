from backend.database import get_db
import sys

# Force encoding
sys.stdout.reconfigure(encoding='utf-8')

db = get_db()
users = db.get_users()
for u in users:
    print(f"ID: {u.id}, Name: {getattr(u, 'name', 'N/A')}, Email: {getattr(u, 'email', 'N/A')}")

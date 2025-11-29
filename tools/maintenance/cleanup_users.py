"""
Clean up database - keep only Daniela Silva and Wilson Rodrigues (specific ID).
"""

from backend.database import Database

# Initialize database
db = Database("data/lesson_planner.db")

print("=" * 70)
print("Database Cleanup - Remove Duplicate Users")
print("=" * 70)
print()

# Get all users
all_users = db.list_users()
print(f"Current users in database: {len(all_users)}")
print()

# Users to keep
keep_users = {
    "Daniela Silva": None,
    "Wilson Rodrigues": "04fe8898-cb89-4a73-affb-64a97a98f820"
}

users_to_keep = []
users_to_delete = []

for user in all_users:
    if user['name'] == "Daniela Silva":
        users_to_keep.append(user)
        print(f"✓ Keeping: {user['name']} (ID: {user['id'][:8]}...)")
    elif user['name'] == "Wilson Rodrigues" and user['id'] == "04fe8898-cb89-4a73-affb-64a97a98f820":
        users_to_keep.append(user)
        print(f"✓ Keeping: {user['name']} (ID: {user['id'][:8]}...)")
    else:
        users_to_delete.append(user)
        print(f"✗ Will delete: {user['name']} (ID: {user['id'][:8]}...)")

print()
print(f"Users to keep: {len(users_to_keep)}")
print(f"Users to delete: {len(users_to_delete)}")
print()

if users_to_delete:
    response = input(f"Delete {len(users_to_delete)} users? (yes/no): ")
    
    if response.lower() == 'yes':
        print()
        print("Deleting users...")
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for user in users_to_delete:
                try:
                    # Delete user (CASCADE will delete related slots and plans)
                    cursor.execute("DELETE FROM users WHERE id = ?", (user['id'],))
                    print(f"  ✓ Deleted: {user['name']} (ID: {user['id'][:8]}...)")
                except Exception as e:
                    print(f"  ✗ Error deleting {user['name']}: {e}")
            
            conn.commit()
        
        print()
        print("=" * 70)
        print("Cleanup Complete!")
        print("=" * 70)
        
        # Show remaining users
        remaining_users = db.list_users()
        print(f"\nRemaining users: {len(remaining_users)}")
        for user in remaining_users:
            # Get counts
            slots = db.get_user_slots(user['id'])
            plans = db.get_user_plans(user['id'])
            
            print(f"  - {user['name']}")
            print(f"    ID: {user['id']}")
            print(f"    Email: {user.get('email', 'N/A')}")
            print(f"    Slots: {len(slots)}")
            print(f"    Plans: {len(plans)}")
            print()
    else:
        print("Cleanup cancelled.")
else:
    print("No users to delete. Database is already clean!")

print()


import os
import uuid
import time
from supabase import create_client, Client

# Project 1 (Wilson)
url1 = "https://eurwhoiqrzcwybjfxoas.supabase.co"
key1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1cndob2lxcnpjd3liamZ4b2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0Njg2OTcsImV4cCI6MjA3ODA0NDY5N30.4NpKiAKjNHkNzSkhokrTO2rZ-kkN-8oEttOiV-0Qnnk"

# Project 2 (Daniela)
url2 = "https://aexkvfjhzwruurwirmah.supabase.co"
key2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFleGt2ZmpoendydXVyd2lybWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0NjY1OTAsImV4cCI6MjA3ODA0MjU5MH0.fr750vnxF6_0UB1UnS5AcL__EtLEEHlrNTLMtVE80Qk"

def ensure_user(name, url, key, email):
    print(f"Checking {name}...")
    try:
        supabase: Client = create_client(url, key)
        response = supabase.table("users").select("*").execute()
        
        if len(response.data) == 0:
            print(f"  No users found. Creating user: {name}")
            user_id = str(uuid.uuid4())
            current_time = int(time.time() * 1000) # ms
            
            new_user = {
                "id": user_id,
                "name": name,
                "email": email,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            try:
                supabase.table("users").insert(new_user).execute()
                print("  User created successfully.")
            except Exception as insert_error:
                print(f"  Failed to insert user: {insert_error}")
                # Try without timestamps if schema differs
                try:
                    print("  Retrying with minimal fields...")
                    minimal_user = {
                        "id": user_id,
                        "name": name,
                        "email": email
                    }
                    supabase.table("users").insert(minimal_user).execute()
                    print("  User created with minimal fields.")
                except Exception as e2:
                    print(f"  Retry failed: {e2}")
        else:
            print(f"  Users found: {len(response.data)}")
            for user in response.data:
                print(f"    - {user}")

    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    ensure_user("Wilson Rodrigues", url1, key1, "wilson@example.com")
    ensure_user("Daniela Silva", url2, key2, "daniela@example.com")


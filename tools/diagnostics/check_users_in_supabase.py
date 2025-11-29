
import os
from supabase import create_client, Client

# Project 1 (Wilson)
url1 = "https://eurwhoiqrzcwybjfxoas.supabase.co"
key1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1cndob2lxcnpjd3liamZ4b2FzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0Njg2OTcsImV4cCI6MjA3ODA0NDY5N30.4NpKiAKjNHkNzSkhokrTO2rZ-kkN-8oEttOiV-0Qnnk"

# Project 2 (Daniela)
url2 = "https://aexkvfjhzwruurwirmah.supabase.co"
key2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFleGt2ZmpoendydXVyd2lybWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0NjY1OTAsImV4cCI6MjA3ODA0MjU5MH0.fr750vnxF6_0UB1UnS5AcL__EtLEEHlrNTLMtVE80Qk"

def check_project(name, url, key):
    print(f"Checking {name}...")
    try:
        supabase: Client = create_client(url, key)
        response = supabase.table("users").select("*").execute()
        print(f"  Users found: {len(response.data)}")
        for user in response.data:
            print(f"    - {user}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    check_project("Project 1", url1, key1)
    check_project("Project 2", url2, key2)


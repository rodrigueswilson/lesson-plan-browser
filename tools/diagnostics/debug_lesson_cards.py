#!/usr/bin/env python3
"""Debug script to check if backend is returning schedule data"""

import requests
import json
import sys

def test_schedule_api():
    """Test the schedule API endpoints"""
    
    BASE_URL = "http://localhost:8000"
    
    # Test users
    test_users = ["test_user", "wilson", "daniela"]
    
    for user_id in test_users:
        print(f"\n=== Testing user: {user_id} ===")
        
        # Test each day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        
        for day in days:
            try:
                response = requests.get(f"{BASE_URL}/api/schedule/{user_id}/{day}")
                print(f"  {day}: {response.status_code} - {len(response.json())} entries")
                
                if response.status_code == 200 and response.json():
                    # Show first entry details
                    first_entry = response.json()[0]
                    print(f"    First entry: {first_entry.get('subject')} ({first_entry.get('start_time')})")
                    
            except Exception as e:
                print(f"  {day}: ERROR - {e}")
    
    # Test plans
    print(f"\n=== Testing plans ===")
    for user_id in test_users:
        try:
            response = requests.get(f"{BASE_URL}/api/plans?user_id={user_id}&limit=10&requester_id={user_id}")
            plans = response.json()
            print(f"  {user_id}: {len(plans.get('data', []))} plans")
            
            if plans.get("data"):
                for plan in plans["data"][:2]:  # Show first 2 plans
                    print(f"    - {plan.get('week_of')} (ID: {plan.get('id')})")
                    
        except Exception as e:
            print(f"  {user_id}: ERROR - {e}")

if __name__ == "__main__":
    test_schedule_api()

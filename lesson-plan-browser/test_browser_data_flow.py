"""
Test suite for Browser App Data Flow
Tests API endpoints used by the lesson-plan-browser app to ensure
data flows correctly from database/JSON files to browser views.

Run this before starting the Tauri app to verify backend is ready.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

# API base URL
API_BASE_URL = "http://localhost:8000/api"

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    if passed:
        test_results["passed"].append(name)
        print(f"✅ {name}")
        if message:
            print(f"   {message}")
    else:
        test_results["failed"].append(name)
        print(f"❌ {name}")
        if message:
            print(f"   Error: {message}")

def log_warning(name: str, message: str):
    """Log warning"""
    test_results["warnings"].append(f"{name}: {message}")
    print(f"⚠️  {name}: {message}")

def test_health_check():
    """Test 1: Health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                log_test("Health Check", True, f"Version: {data.get('version', 'unknown')}")
                return True
            else:
                log_test("Health Check", False, f"Unexpected status: {data.get('status')}")
                return False
        else:
            log_test("Health Check", False, f"HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        log_test("Health Check", False, "Backend not running on http://localhost:8000")
        return False
    except Exception as e:
        log_test("Health Check", False, str(e))
        return False

def test_users_list():
    """Test 2: List users endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            if isinstance(users, list):
                log_test("List Users", True, f"Found {len(users)} user(s)")
                if len(users) > 0:
                    log_warning("Users Available", f"Found users in database. First: {users[0].get('name', 'Unknown')}")
                    return users[0].get("id") if users else None
                else:
                    log_warning("No Users", "Database is empty. App will show empty user selector.")
                    return None
            else:
                log_test("List Users", False, "Response is not a list")
                return None
        else:
            log_test("List Users", False, f"HTTP {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        log_test("List Users", False, str(e))
        return None

def test_user_get(user_id: str):
    """Test 3: Get single user"""
    if not user_id:
        log_warning("Get User", "Skipped - no users available")
        return None
    
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}", timeout=10)
        if response.status_code == 200:
            user = response.json()
            required_fields = ["id", "name", "first_name", "last_name", "created_at"]
            missing = [f for f in required_fields if f not in user]
            if not missing:
                log_test("Get User", True, f"User: {user.get('name')}")
                return user
            else:
                log_test("Get User", False, f"Missing fields: {missing}")
                return None
        else:
            log_test("Get User", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        log_test("Get User", False, str(e))
        return None

def test_recent_weeks(user_id: str):
    """Test 4: Get recent weeks (JSON file detection)"""
    if not user_id:
        log_warning("Recent Weeks", "Skipped - no users available")
        return []
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/recent-weeks",
            params={"user_id": user_id, "limit": 10},
            timeout=10
        )
        if response.status_code == 200:
            weeks = response.json()
            if isinstance(weeks, list):
                log_test("Recent Weeks", True, f"Found {len(weeks)} week(s) from JSON files")
                if len(weeks) > 0:
                    log_warning("JSON Files Found", f"Week: {weeks[0].get('week_of', 'Unknown')}")
                return weeks
            else:
                log_test("Recent Weeks", False, "Response is not a list")
                return []
        else:
            log_test("Recent Weeks", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test("Recent Weeks", False, str(e))
        return []

def test_plans_list(user_id: str):
    """Test 5: List lesson plans from database"""
    if not user_id:
        log_warning("List Plans", "Skipped - no users available")
        return []
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}/plans",
            params={"limit": 50},
            timeout=10
        )
        if response.status_code == 200:
            plans = response.json()
            if isinstance(plans, list):
                log_test("List Plans", True, f"Found {len(plans)} plan(s) in database")
                if len(plans) > 0:
                    log_warning("Plans Found", f"Latest plan: {plans[0].get('week_of', 'Unknown')}")
                    return plans
                else:
                    log_warning("No Plans", "Database has no lesson plans")
                    return []
            else:
                log_test("List Plans", False, "Response is not a list")
                return []
        else:
            log_test("List Plans", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test("List Plans", False, str(e))
        return []

def test_plan_detail(plan_id: str, user_id: str):
    """Test 6: Get plan detail with lesson_json"""
    if not plan_id:
        log_warning("Plan Detail", "Skipped - no plans available")
        return None
    
    try:
        response = requests.get(f"{API_BASE_URL}/plans/{plan_id}", timeout=10)
        if response.status_code == 200:
            plan = response.json()
            required_fields = ["id", "user_id", "week_of", "lesson_json", "status"]
            missing = [f for f in required_fields if f not in plan]
            if not missing:
                lesson_json = plan.get("lesson_json")
                if lesson_json:
                    log_test("Plan Detail", True, f"Plan {plan.get('week_of')} has lesson_json")
                    return plan
                else:
                    log_warning("Plan Detail", f"Plan {plan.get('week_of')} has no lesson_json")
                    return plan
            else:
                log_test("Plan Detail", False, f"Missing fields: {missing}")
                return None
        else:
            log_test("Plan Detail", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        log_test("Plan Detail", False, str(e))
        return None

def test_schedule_get(user_id: str):
    """Test 7: Get schedule entries"""
    if not user_id:
        log_warning("Get Schedule", "Skipped - no users available")
        return []
    
    try:
        response = requests.get(f"{API_BASE_URL}/schedules/{user_id}", timeout=10)
        if response.status_code == 200:
            entries = response.json()
            if isinstance(entries, list):
                log_test("Get Schedule", True, f"Found {len(entries)} schedule entry/entries")
                if len(entries) > 0:
                    # Check for different days
                    days = set(e.get("day_of_week") for e in entries if e.get("day_of_week"))
                    log_warning("Schedule Entries", f"Days with entries: {', '.join(days) if days else 'None'}")
                return entries
            else:
                log_test("Get Schedule", False, "Response is not a list")
                return []
        else:
            log_test("Get Schedule", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test("Get Schedule", False, str(e))
        return []

def test_schedule_get_day(user_id: str, day: str = "monday"):
    """Test 8: Get schedule for specific day"""
    if not user_id:
        log_warning("Get Schedule Day", "Skipped - no users available")
        return []
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/schedules/{user_id}",
            params={"day_of_week": day},
            timeout=10
        )
        if response.status_code == 200:
            entries = response.json()
            if isinstance(entries, list):
                log_test(f"Get Schedule ({day.title()})", True, f"Found {len(entries)} entry/entries")
                return entries
            else:
                log_test(f"Get Schedule ({day.title()})", False, "Response is not a list")
                return []
        else:
            log_test(f"Get Schedule ({day.title()})", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test(f"Get Schedule ({day.title()})", False, str(e))
        return []

def test_current_lesson(user_id: str):
    """Test 9: Get current lesson"""
    if not user_id:
        log_warning("Current Lesson", "Skipped - no users available")
        return None
    
    try:
        response = requests.get(f"{API_BASE_URL}/schedules/{user_id}/current", timeout=10)
        if response.status_code == 200:
            lesson = response.json()
            if lesson is None:
                log_warning("Current Lesson", "No current lesson (outside class hours)")
                return None
            else:
                log_test("Current Lesson", True, f"Current: {lesson.get('subject', 'Unknown')} at {lesson.get('start_time', 'Unknown')}")
                return lesson
        else:
            log_test("Current Lesson", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        log_test("Current Lesson", False, str(e))
        return None

def test_slots_list(user_id: str):
    """Test 10: List class slots"""
    if not user_id:
        log_warning("List Slots", "Skipped - no users available")
        return []
    
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/slots", timeout=10)
        if response.status_code == 200:
            slots = response.json()
            if isinstance(slots, list):
                log_test("List Slots", True, f"Found {len(slots)} slot(s)")
                return slots
            else:
                log_test("List Slots", False, "Response is not a list")
                return []
        else:
            log_test("List Slots", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test("List Slots", False, str(e))
        return []

def test_lesson_steps(plan_id: str, day: str = "monday", slot: int = 1, user_id: Optional[str] = None):
    """Test 11: Get lesson steps"""
    if not plan_id:
        log_warning("Lesson Steps", "Skipped - no plans available")
        return []
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/lesson-steps/{plan_id}/{day}/{slot}",
            timeout=10
        )
        if response.status_code == 200:
            steps = response.json()
            if isinstance(steps, list):
                log_test("Get Lesson Steps", True, f"Found {len(steps)} step(s)")
                return steps
            else:
                log_test("Get Lesson Steps", False, "Response is not a list")
                return []
        elif response.status_code == 404:
            log_warning("Lesson Steps", f"No steps found for plan {plan_id} (may need generation)")
            return []
        else:
            log_test("Get Lesson Steps", False, f"HTTP {response.status_code}")
            return []
    except Exception as e:
        log_test("Get Lesson Steps", False, str(e))
        return []

def test_lesson_mode_session_active(user_id: str):
    """Test 12: Get active lesson mode session"""
    if not user_id:
        log_warning("Active Session", "Skipped - no users available")
        return None
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/lesson-mode/session/active",
            params={"user_id": user_id},
            timeout=10
        )
        if response.status_code == 200:
            session = response.json()
            if session is None:
                log_warning("Active Session", "No active session (expected if not in Lesson Mode)")
                return None
            else:
                log_test("Active Session", True, f"Session ID: {session.get('id', 'Unknown')}")
                return session
        else:
            log_test("Active Session", False, f"HTTP {response.status_code}")
            return None
    except Exception as e:
        log_test("Active Session", False, str(e))
        return None

def test_data_flow_integration(user_id: str):
    """Test 13: Full data flow integration test"""
    if not user_id:
        log_warning("Data Flow Integration", "Skipped - no users available")
        return False
    
    print("\n🔄 Testing full data flow...")
    
    # 1. Get plans
    plans = test_plans_list(user_id)
    if not plans:
        log_warning("Data Flow", "No plans found - cannot test full flow")
        return False
    
    plan = plans[0]
    plan_id = plan.get("id")
    
    # 2. Get plan detail
    plan_detail = test_plan_detail(plan_id, user_id)
    if not plan_detail:
        log_warning("Data Flow", "Could not get plan detail")
        return False
    
    # 3. Get schedule
    schedule = test_schedule_get(user_id)
    if not schedule:
        log_warning("Data Flow", "No schedule entries found")
        return False
    
    # 4. Try to get lesson steps (may not exist)
    lesson_json = plan_detail.get("lesson_json")
    if lesson_json and isinstance(lesson_json, dict):
        days = lesson_json.get("days", {})
        if days:
            first_day = list(days.keys())[0]
            slots = days.get(first_day, {})
            if slots:
                first_slot = list(slots.keys())[0]
                slot_num = int(first_slot) if first_slot.isdigit() else 1
                test_lesson_steps(plan_id, first_day, slot_num, user_id)
    
    log_test("Data Flow Integration", True, "All components connected successfully")
    return True

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    print()
    
    if test_results['failed']:
        print("Failed Tests:")
        for test in test_results['failed']:
            print(f"  - {test}")
        print()
    
    if test_results['warnings']:
        print("Warnings:")
        for warning in test_results['warnings']:
            print(f"  - {warning}")
        print()
    
    # Determine overall status
    if len(test_results['failed']) == 0:
        print("✅ ALL TESTS PASSED - Backend is ready for browser app!")
        return True
    else:
        print("❌ SOME TESTS FAILED - Fix backend issues before running app")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("BROWSER APP DATA FLOW TEST SUITE")
    print("="*60)
    print(f"Testing API endpoints at: {API_BASE_URL}")
    print()
    
    # Test 1: Health check (must pass for other tests)
    if not test_health_check():
        print("\n❌ Backend is not running or not accessible!")
        print("   Start backend with: python -m uvicorn backend.api:app --reload --port 8000")
        return False
    
    print()
    print("Testing Browser App Endpoints...")
    print("-" * 60)
    
    # Test 2: Get users
    user_id = test_users_list()
    user = None
    
    if user_id:
        # Test 3: Get user details
        user = test_user_get(user_id)
        
        # Test 4: Recent weeks (JSON files)
        test_recent_weeks(user_id)
        
        # Test 5: List plans
        plans = test_plans_list(user_id)
        
        # Test 6: Plan detail
        plan_id = plans[0].get("id") if plans else None
        if plan_id:
            test_plan_detail(plan_id, user_id)
        
        # Test 7-8: Schedule
        test_schedule_get(user_id)
        test_schedule_get_day(user_id, "monday")
        
        # Test 9: Current lesson
        test_current_lesson(user_id)
        
        # Test 10: Slots
        test_slots_list(user_id)
        
        # Test 11: Lesson steps (if plan available)
        if plan_id:
            test_lesson_steps(plan_id, "monday", 1, user_id)
        
        # Test 12: Active session
        test_lesson_mode_session_active(user_id)
        
        # Test 13: Integration
        test_data_flow_integration(user_id)
    else:
        print("\n⚠️  No users found - some tests skipped")
        print("   Create a user first, or tests will show empty data (which is OK)")
    
    # Print summary
    return print_summary()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


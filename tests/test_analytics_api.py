"""
Test script for analytics API endpoints.
Requires backend running at localhost:8000; skips when server is not available.
"""

import json

import pytest
import requests

API_BASE = "http://localhost:8000/api"


def _get_or_skip(url, timeout=1):
    """GET url; skip test if backend is not running."""
    try:
        return requests.get(url, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        pytest.skip(f"Backend not running at {API_BASE}: {e}")


def test_analytics_summary():
    """Test analytics summary endpoint."""
    print("\n=== Testing Analytics Summary ===")
    response = _get_or_skip(f"{API_BASE}/analytics/summary?days=30")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Plans: {data.get('total_plans') or 0}")
        print(f"Total Operations: {data.get('total_operations') or 0}")
        total_cost = data.get('total_cost_usd') or 0
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Model Distribution: {len(data.get('model_distribution', []))} models")
        print(f"Operation Breakdown: {len(data.get('operation_breakdown', []))} types")
        print("SUCCESS")
    else:
        print(f"ERROR: {response.text}")

def test_analytics_daily():
    """Test daily analytics endpoint."""
    print("\n=== Testing Daily Analytics ===")
    response = _get_or_skip(f"{API_BASE}/analytics/daily?days=30")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Days with data: {len(data)}")
        if data:
            print(f"Sample day: {data[0]}")
        print("SUCCESS")
    else:
        print(f"ERROR: {response.text}")

def test_analytics_export():
    """Test CSV export endpoint."""
    print("\n=== Testing Analytics Export ===")
    response = _get_or_skip(f"{API_BASE}/analytics/export?days=30")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        csv_data = response.text
        lines = csv_data.split('\n')
        print(f"CSV Lines: {len(lines)}")
        print(f"Header: {lines[0] if lines else 'N/A'}")
        print("SUCCESS")
    elif response.status_code == 404:
        print("No data available (expected if no plans processed yet)")
    else:
        print(f"ERROR: {response.text}")

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Check ===")
    response = _get_or_skip(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        print("SUCCESS")
    else:
        print(f"ERROR: {response.text}")

if __name__ == "__main__":
    print("Testing Analytics API Endpoints")
    print("=" * 50)
    
    try:
        test_health()
        test_analytics_summary()
        test_analytics_daily()
        test_analytics_export()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to backend. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"\nERROR: {e}")

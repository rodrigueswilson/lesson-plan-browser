"""Test if avg_duration_per_plan_ms is in the API response."""

import requests

response = requests.get("http://localhost:8000/api/analytics/summary?days=30")
data = response.json()

print("\n=== API Response Fields ===\n")
for key, value in data.items():
    if not isinstance(value, (list, dict)):
        print(f"{key}: {value}")

print("\n=== Check for new field ===")
if 'avg_duration_per_plan_ms' in data:
    print(f"✓ avg_duration_per_plan_ms: {data['avg_duration_per_plan_ms']}")
else:
    print("✗ avg_duration_per_plan_ms NOT FOUND")
    print("\nBackend needs to be restarted to pick up the new field!")

import sys
sys.path.insert(0, '.')
from backend.api import app

print("Checking routes...")
routes = [r.path for r in app.routes]
recent_routes = [r for r in routes if 'recent' in r.lower() or 'week' in r.lower()]

print(f"\nTotal routes: {len(routes)}")
print(f"\nRoutes with 'recent' or 'week':")
for route in recent_routes:
    print(f"  {route}")

if '/api/recent-weeks' in routes:
    print("\n✓ /api/recent-weeks endpoint EXISTS")
else:
    print("\n✗ /api/recent-weeks endpoint NOT FOUND")

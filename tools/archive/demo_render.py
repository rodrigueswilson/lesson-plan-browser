"""Quick demo script to render a lesson plan"""
import requests
import json
import time

# Load the example
with open('tests/fixtures/valid_lesson_minimal.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 60)
print("DEMO: Rendering Lesson Plan")
print("=" * 60)

# Validate first
print("\n1. Validating JSON...")
start = time.time()
response = requests.post(
    'http://localhost:8000/api/validate',
    json={'json_data': data}
)
validation_time = (time.time() - start) * 1000
result = response.json()

if result['valid']:
    print(f"   ✅ Valid! ({validation_time:.2f}ms)")
else:
    print(f"   ❌ Invalid!")
    print(f"   Errors: {result.get('errors')}")
    exit(1)

# Render
print("\n2. Generating DOCX...")
start = time.time()
response = requests.post(
    'http://localhost:8000/api/render',
    json={'json_data': data, 'output_filename': 'demo_lesson_plan.docx'},
    timeout=30
)
total_time = (time.time() - start) * 1000
result = response.json()

if result['success']:
    print(f"   ✅ Success!")
    print(f"   Output: {result['output_path']}")
    print(f"   Size: {result['file_size']:,} bytes")
    print(f"   Render time: {result['render_time_ms']:.2f}ms")
    print(f"   Total time: {total_time:.2f}ms")
else:
    print(f"   ❌ Failed!")
    print(f"   Error: {result.get('error')}")

print("\n" + "=" * 60)
print("DEMO COMPLETE")
print("=" * 60)
print("\nYou can now open the file:")
print(f"  {result.get('output_path', 'output/demo_lesson_plan.docx')}")

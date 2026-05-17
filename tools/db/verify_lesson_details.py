import urllib.request
import json

lesson_id = "Math_3_U2_1hBoK4uk_L1"
url = f"http://localhost:8000/api/curriculum/lessons/{lesson_id}"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(f"Lesson Details for {lesson_id}:")
        print(f"  Title: {data.get('title')}")
        print(f"  Procedure HTML Size: {len(data.get('procedure_html', ''))} bytes")
        print(f"  First 200 chars: {data.get('procedure_html', '')[:200]}")

except Exception as e:
    print(f"Error: {e}")

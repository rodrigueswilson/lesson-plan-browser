import urllib.request
import json

url = "http://localhost:8000/api/curriculum/units/Math_3_U2_1hBoK4uk/lessons"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        print(f"Total Lessons: {len(data)}")
        for l in data[:5]:
            print(f"Lesson {l.get('lesson_number')}: {len(l.get('procedure_html', ''))} bytes")
        
        # Check Unit Intro
        intro_url = "http://localhost:8000/api/curriculum/units/Math_3_U2_1hBoK4uk/intro"
        with urllib.request.urlopen(intro_url) as intro_resp:
            intro_data = json.loads(intro_resp.read().decode())
            print(f"Unit Intro Found: {bool(intro_data)}")
            print(f"Unit Intro Size: {len(intro_data.get('procedure_html', ''))} bytes")

except Exception as e:
    print(f"Error: {e}")

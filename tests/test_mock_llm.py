"""
Test Mock LLM Service
"""

import requests
import json

PRIMARY_CONTENT = """
MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.

Anticipatory Set: Show ice cube melting in a beaker.

Instruction: Present three states of matter with demonstrations.

Assessment: Students complete three-column chart.

Homework: Find 5 examples of each state of matter at home.
"""

def test_mock_llm():
    print("=" * 60)
    print("TESTING MOCK LLM SERVICE")
    print("=" * 60)
    print()
    
    # Prepare request - no API key needed for mock
    request_data = {
        "primary_content": PRIMARY_CONTENT,
        "grade": "6",
        "subject": "Science",
        "week_of": "10/6-10/10",
        "teacher_name": "Ms. Rodriguez",
        "homeroom": "302",
        "provider": "mock"  # Use mock provider
    }
    
    print("📤 Sending transformation request (using MOCK service)...")
    print(f"   Grade: {request_data['grade']}")
    print(f"   Subject: {request_data['subject']}")
    print(f"   Week: {request_data['week_of']}")
    print()
    
    try:
        # Call API
        response = requests.post(
            'http://localhost:8000/api/transform',
            json=request_data,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('success'):
            print("✅ Transformation successful!")
            print(f"   Time: {result.get('transform_time_ms', 0):.2f}ms")
            print()
            
            # Get the lesson JSON
            lesson_json = result.get('lesson_json')
            
            if lesson_json:
                # Save to file
                with open('output/mock_test_lesson.json', 'w', encoding='utf-8') as f:
                    json.dump(lesson_json, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved to: output/mock_test_lesson.json")
                print()
                
                # Validate
                print("🔍 Validating generated JSON...")
                validate_response = requests.post(
                    'http://localhost:8000/api/validate',
                    json={'json_data': lesson_json},
                    timeout=10
                )
                
                validate_result = validate_response.json()
                
                if validate_result.get('valid'):
                    print("✅ Validation PASSED!")
                    print()
                    
                    # Render to DOCX
                    print("📄 Rendering to DOCX...")
                    render_response = requests.post(
                        'http://localhost:8000/api/render',
                        json={
                            'json_data': lesson_json,
                            'output_filename': 'mock_test_lesson.docx'
                        },
                        timeout=30
                    )
                    
                    render_result = render_response.json()
                    
                    if render_result.get('success'):
                        print("✅ DOCX generated successfully!")
                        print(f"   Output: {render_result.get('output_path')}")
                        print(f"   Size: {render_result.get('file_size'):,} bytes")
                        print(f"   Time: {render_result.get('render_time_ms'):.2f}ms")
                        print()
                        print("🎉 COMPLETE END-TO-END SUCCESS (with MOCK LLM)!")
                    else:
                        print(f"❌ Rendering failed: {render_result.get('error')}")
                else:
                    print("❌ Validation FAILED!")
                    print(f"   Errors: {validate_result.get('errors', [])}")
            else:
                print("❌ No lesson JSON in response")
        else:
            print("❌ Transformation failed!")
            print(f"   Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print()
    print("NOTE: This used a MOCK LLM service (no real API calls)")
    print("To use real OpenAI, add a valid API key to api_key.txt")

if __name__ == "__main__":
    test_mock_llm()

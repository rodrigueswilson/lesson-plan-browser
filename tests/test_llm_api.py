"""
Test LLM transformation via API endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Sample primary teacher content
PRIMARY_CONTENT = """
MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.

Anticipatory Set: Show ice cube melting in a beaker. Ask: What is happening? Why? Record observations.

Instruction: 
- Present three states of matter with demonstrations
- Show solid (ice), liquid (water), gas (steam)
- Discuss molecular movement in each state
- Students complete comparison chart

Misconceptions: Students may think gases have no mass or that liquids always take the shape of their container from the bottom up.

Assessment: Students complete three-column chart comparing states of matter. Must include at least 3 properties for each state.

Homework: Find 5 examples of each state of matter at home. Draw or photograph them. Label in English.
"""

def test_transform_api(api_key=None):
    """Test the /api/transform endpoint"""
    
    print("=" * 60)
    print("TESTING LLM TRANSFORMATION API")
    print("=" * 60)
    print()
    
    # Check for API key
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
    
    # Try reading from file if not in environment
    if not api_key:
        try:
            with open('api_key.txt', 'r') as f:
                api_key = f.read().strip()
            print("📁 API key loaded from api_key.txt")
        except:
            pass
    
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        print("\nSet it with:")
        print("  set OPENAI_API_KEY=your-key-here")
        print("Or create api_key.txt with your key")
        print("Or pass it to the function: test_transform_api('your-key')")
        return
    
    print(f"✅ API key found: {api_key[:20]}...")
    print()
    
    # Set in environment for the API to use
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Prepare request
    request_data = {
        "primary_content": PRIMARY_CONTENT,
        "grade": "6",
        "subject": "Science",
        "week_of": "10/6-10/10",
        "teacher_name": "Ms. Rodriguez",
        "homeroom": "302",
        "provider": "openai"
    }
    
    print("📤 Sending transformation request...")
    print(f"   Grade: {request_data['grade']}")
    print(f"   Subject: {request_data['subject']}")
    print(f"   Week: {request_data['week_of']}")
    print()
    
    try:
        # Call API
        response = requests.post(
            'http://localhost:8000/api/transform',
            json=request_data,
            timeout=60  # LLM calls can take time
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
                output_file = 'output/llm_api_test_lesson.json'
                os.makedirs('output', exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(lesson_json, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Saved to: {output_file}")
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
                            'output_filename': 'llm_api_test_lesson.docx'
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
                        print("🎉 COMPLETE END-TO-END SUCCESS!")
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
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (LLM taking too long)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_transform_api()

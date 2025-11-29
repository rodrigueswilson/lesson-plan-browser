"""
Test LLM Workflow - Validate prompt_v4.md transformation
"""

import os
from openai import OpenAI
import json
from pathlib import Path

# Sample primary teacher lesson content
PRIMARY_TEACHER_CONTENT = """
Week of: 10/6-10/10
Grade: 6
Subject: Science
Teacher: Ms. Johnson

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

def load_prompt_template():
    """Load the prompt_v4.md framework"""
    with open('prompt_v4.md', 'r', encoding='utf-8') as f:
        return f.read()

def load_schema():
    """Load the JSON output schema"""
    with open('schemas/lesson_output_schema.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def test_llm_transformation(api_key: str = None):
    """Test the LLM transformation with prompt_v4"""
    
    # Check for API key
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found!")
        print("Set OPENAI_API_KEY environment variable or pass api_key parameter")
        return None
    
    # Load prompt template
    print("📖 Loading prompt_v4.md framework...")
    prompt_template = load_prompt_template()
    
    # Load schema
    print("📋 Loading JSON schema...")
    schema = load_schema()
    
    # Configure for Grade 6
    grade_level = "6th grade"
    prompt_template = prompt_template.replace('[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]', f'[GRADE_LEVEL_VARIABLE = {grade_level}]')
    
    # Enable JSON output mode
    system_config = """
SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output pure JSON matching schemas/lesson_output_schema.json
- No markdown code blocks
- No text before or after JSON
"""
    
    # Build the complete prompt
    full_prompt = f"""{system_config}

{prompt_template}

---

PRIMARY TEACHER LESSON PLAN:

{PRIMARY_TEACHER_CONTENT}

---

TASK: Transform this primary teacher lesson plan into a bilingual lesson plan following the framework above.

REQUIREMENTS:
1. Output ONLY valid JSON (no markdown, no code blocks)
2. Include all required fields from the schema
3. Generate WIDA-aligned objectives
4. Select appropriate co-teaching model
5. Add bilingual bridges with Portuguese cognates
6. Include 3-5 ELL support strategies
7. Add linguistic misconception notes
8. Create bilingual assessment overlay
9. Add family connection in homework

Generate the complete bilingual lesson plan now.
"""
    
    # Initialize OpenAI client
    print("🤖 Connecting to OpenAI API...")
    client = OpenAI(api_key=api_key)
    
    # Make API call
    print("⚡ Sending request to GPT-4...")
    print(f"   Prompt length: {len(full_prompt):,} characters")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # or "gpt-4" or "gpt-3.5-turbo"
            messages=[
                {
                    "role": "system",
                    "content": "You are a bilingual education specialist. Output only valid JSON."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        # Extract response
        llm_output = response.choices[0].message.content
        
        print("✅ Received response from LLM")
        print(f"   Response length: {len(llm_output):,} characters")
        
        # Try to parse as JSON
        print("\n📝 Parsing JSON response...")
        try:
            # Clean up if wrapped in code blocks
            if llm_output.strip().startswith('```'):
                llm_output = llm_output.strip()
                llm_output = llm_output.replace('```json', '').replace('```', '').strip()
            
            lesson_json = json.loads(llm_output)
            print("✅ Valid JSON received!")
            
            # Save to file
            output_file = 'output/llm_test_lesson.json'
            os.makedirs('output', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(lesson_json, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved to: {output_file}")
            
            # Validate against schema
            print("\n🔍 Validating against schema...")
            # TODO: Add schema validation here
            
            return lesson_json
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("\nRaw response:")
            print(llm_output[:500] + "..." if len(llm_output) > 500 else llm_output)
            return None
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return None

def validate_with_api(lesson_json):
    """Validate the generated JSON using our API"""
    import requests
    
    print("\n🔍 Validating with local API...")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/validate',
            json={'json_data': lesson_json},
            timeout=10
        )
        
        result = response.json()
        
        if result.get('valid'):
            print("✅ Validation PASSED!")
            return True
        else:
            print("❌ Validation FAILED!")
            print(f"Errors: {result.get('errors', [])}")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def render_with_api(lesson_json):
    """Render the JSON to DOCX using our API"""
    import requests
    
    print("\n📄 Rendering to DOCX...")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/render',
            json={
                'json_data': lesson_json,
                'output_filename': 'llm_test_lesson.docx'
            },
            timeout=30
        )
        
        result = response.json()
        
        if result.get('success'):
            print("✅ DOCX generated successfully!")
            print(f"   Output: {result.get('output_path')}")
            print(f"   Size: {result.get('file_size'):,} bytes")
            print(f"   Time: {result.get('render_time_ms'):.2f}ms")
            return True
        else:
            print(f"❌ Rendering failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Rendering error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("LLM WORKFLOW TEST")
    print("=" * 60)
    print()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  No OPENAI_API_KEY found in environment")
        print("\nTo run this test:")
        print("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Set it as environment variable:")
        print("   Windows: set OPENAI_API_KEY=your-key-here")
        print("   Or pass it to the function: test_llm_transformation('your-key')")
        print()
        exit(1)
    
    # Run test
    lesson_json = test_llm_transformation(api_key)
    
    if lesson_json:
        # Validate
        if validate_with_api(lesson_json):
            # Render
            render_with_api(lesson_json)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

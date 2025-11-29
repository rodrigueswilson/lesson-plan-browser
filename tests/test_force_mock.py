"""
Force Mock Service Test - Bypasses API entirely
"""

from backend.mock_llm_service import get_mock_llm_service
import json

PRIMARY_CONTENT = """
MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.
"""

print("=" * 60)
print("DIRECT MOCK SERVICE TEST")
print("=" * 60)
print()

# Get mock service directly
mock_service = get_mock_llm_service()

# Transform
success, lesson_json, error = mock_service.transform_lesson(
    primary_content=PRIMARY_CONTENT,
    grade="6",
    subject="Science",
    week_of="10/6-10/10",
    teacher_name="Ms. Rodriguez",
    homeroom="302"
)

if success:
    print("✅ Mock transformation successful!")
    print()
    
    # Save
    with open('output/direct_mock_lesson.json', 'w', encoding='utf-8') as f:
        json.dump(lesson_json, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to: output/direct_mock_lesson.json")
    print()
    
    # Show structure
    print("📋 Generated structure:")
    print(f"   Metadata: {lesson_json.get('metadata', {})}")
    print(f"   Days: {list(lesson_json.get('days', {}).keys())}")
    print()
    
    # Now validate and render via API
    import requests
    
    print("🔍 Validating...")
    val_response = requests.post(
        'http://localhost:8000/api/validate',
        json={'json_data': lesson_json}
    )
    
    if val_response.json().get('valid'):
        print("✅ Valid!")
        print()
        
        print("📄 Rendering to DOCX...")
        render_response = requests.post(
            'http://localhost:8000/api/render',
            json={
                'json_data': lesson_json,
                'output_filename': 'direct_mock_lesson.docx'
            }
        )
        
        result = render_response.json()
        if result.get('success'):
            print("✅ DOCX generated!")
            print(f"   Output: {result.get('output_path')}")
            print(f"   Size: {result.get('file_size'):,} bytes")
            print()
            print("🎉 COMPLETE SUCCESS (using direct mock service)!")
        else:
            print(f"❌ Render failed: {result.get('error')}")
    else:
        print(f"❌ Validation failed: {val_response.json().get('errors')}")
else:
    print(f"❌ Failed: {error}")

print()
print("=" * 60)

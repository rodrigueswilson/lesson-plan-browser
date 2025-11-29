"""List all JSON files that contain lesson plans."""
import json
from pathlib import Path

def is_lesson_plan(data):
    """Check if JSON data is a lesson plan structure."""
    if not isinstance(data, dict):
        return False
    
    # Check for lesson plan structure
    has_metadata = 'metadata' in data
    has_days = 'days' in data
    
    # Also check if wrapped
    has_lesson_json = 'lesson_json' in data
    
    return (has_metadata and has_days) or has_lesson_json

def check_json_file(json_path):
    """Check if a JSON file contains a lesson plan."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if it's a lesson plan
        if is_lesson_plan(data):
            # Extract lesson_json if wrapped
            lesson_json = data.get('lesson_json', data)
            
            metadata = lesson_json.get('metadata', {})
            week_of = metadata.get('week_of', 'Unknown')
            grade = metadata.get('grade', 'Unknown')
            subject = metadata.get('subject', 'Unknown')
            teacher = metadata.get('teacher_name', 'Unknown')
            
            # Count objectives
            objectives_count = 0
            days = lesson_json.get('days', {})
            for day_data in days.values():
                slots = day_data.get('slots', [])
                for slot in slots:
                    if slot.get('objective'):
                        objectives_count += 1
            
            return {
                'path': str(json_path),
                'week_of': week_of,
                'grade': grade,
                'subject': subject,
                'teacher': teacher,
                'objectives_count': objectives_count,
                'days': list(days.keys())
            }
    except Exception as e:
        return None

def main():
    """Find all lesson plan JSON files."""
    # Check output directory
    output_dir = Path('output')
    json_files = list(output_dir.glob('*.json'))
    
    lesson_plans = []
    
    print("Scanning JSON files for lesson plans...\n")
    
    for json_file in json_files:
        result = check_json_file(json_file)
        if result:
            lesson_plans.append(result)
    
    if lesson_plans:
        print(f"Found {len(lesson_plans)} lesson plan JSON files:\n")
        print("=" * 80)
        
        for i, plan in enumerate(lesson_plans, 1):
            print(f"\n{i}. {Path(plan['path']).name}")
            print(f"   Path: {plan['path']}")
            print(f"   Week: {plan['week_of']}")
            print(f"   Grade: {plan['grade']}")
            print(f"   Subject: {plan['subject']}")
            print(f"   Teacher: {plan['teacher']}")
            print(f"   Objectives: {plan['objectives_count']}")
            print(f"   Days: {', '.join(plan['days'])}")
        
        print("\n" + "=" * 80)
        print(f"\nTotal: {len(lesson_plans)} lesson plan files found")
    else:
        print("No lesson plan JSON files found in output directory.")

if __name__ == '__main__':
    main()


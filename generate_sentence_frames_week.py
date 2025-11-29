#!/usr/bin/env python3
"""
Generate sentence frames HTML/PDF for all lesson plans in a week folder.
Uses the updated format: '11/17/25 | Wednesday | ELA | Grade 3 | T5'
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.sentence_frames_pdf_generator import (
    SentenceFramesPDFGenerator,
    generate_sentence_frames_html,
    generate_sentence_frames_pdf,
)


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


def find_lesson_plan_files(week_folder: Path):
    """Find all lesson plan JSON files in the week folder."""
    lesson_plans = []
    
    # Look for JSON files recursively
    json_files = list(week_folder.rglob('*.json'))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if it's a lesson plan
            if is_lesson_plan(data):
                # Extract lesson_json if wrapped
                lesson_json = data.get('lesson_json', data)
                
                # Check if it has sentence frames
                has_frames = False
                days = lesson_json.get('days', {})
                for day_data in days.values():
                    # Check day-level frames
                    if day_data.get('sentence_frames'):
                        has_frames = True
                        break
                    # Check slot-level frames
                    slots = day_data.get('slots', [])
                    for slot in slots:
                        if slot.get('sentence_frames'):
                            has_frames = True
                            break
                    if has_frames:
                        break
                
                if has_frames:
                    metadata = lesson_json.get('metadata', {})
                    lesson_plans.append({
                        'path': json_file,
                        'lesson_json': lesson_json,
                        'week_of': metadata.get('week_of', 'Unknown'),
                        'teacher': metadata.get('teacher_name', 'Unknown'),
                    })
        except Exception as e:
            print(f"  Warning: Could not read {json_file.name}: {e}")
            continue
    
    return lesson_plans


def generate_sentence_frames_for_week(week_folder_path: str):
    """Generate sentence frames HTML/PDF for all lesson plans in the week folder."""
    print("=" * 80)
    print("GENERATING SENTENCE FRAMES FOR WEEK")
    print("=" * 80)
    print()
    
    week_folder = Path(week_folder_path)
    
    if not week_folder.exists():
        print(f"Error: Week folder not found: {week_folder_path}")
        return
    
    print(f"Week folder: {week_folder}")
    print()
    
    # Find all lesson plan files
    print("Scanning for lesson plan files with sentence frames...")
    print("-" * 80)
    
    lesson_plans = find_lesson_plan_files(week_folder)
    
    if not lesson_plans:
        print("No lesson plans with sentence frames found in the week folder.")
        return
    
    print(f"Found {len(lesson_plans)} lesson plan(s) with sentence frames:")
    for i, plan in enumerate(lesson_plans, 1):
        print(f"  {i}. {plan['path'].name}")
        print(f"     Week: {plan['week_of']}, Teacher: {plan['teacher']}")
    print()
    
    # Generate sentence frames for each lesson plan
    generator = SentenceFramesPDFGenerator()
    # Save files directly in the week folder root
    output_dir = week_folder
    
    print("Generating sentence frames HTML/PDF...")
    print("-" * 80)
    
    success_count = 0
    error_count = 0
    
    for i, plan in enumerate(lesson_plans, 1):
        print(f"\n[{i}/{len(lesson_plans)}] Processing: {plan['path'].name}")
        
        try:
            # Extract metadata
            metadata = plan['lesson_json'].get('metadata', {})
            teacher_name = metadata.get('teacher_name', 'Unknown')
            
            # Use original filename stem + _sentence_frames suffix
            file_slug = plan['path'].stem  # e.g., "Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906"
            
            # Generate HTML with format: {original_filename}_sentence_frames.html
            html_filename = f"{file_slug}_sentence_frames.html"
            html_path = output_dir / html_filename
            
            html_output = generator.generate_html(
                plan['lesson_json'],
                str(html_path),
                user_name=teacher_name
            )
            
            print(f"  [OK] HTML generated: {html_path.name}")
            
            # Generate PDF
            pdf_filename = html_filename.replace('.html', '.pdf')
            pdf_path = output_dir / pdf_filename
            
            try:
                pdf_output = generator.generate_pdf(
                    plan['lesson_json'],
                    str(pdf_path),
                    user_name=teacher_name,
                    keep_html=True
                )
                print(f"  [OK] PDF generated: {pdf_path.name}")
            except Exception as pdf_error:
                print(f"  [WARN] PDF generation failed: {pdf_error}")
                print(f"     HTML is still available at: {html_path}")
            
            success_count += 1
            
        except Exception as e:
            print(f"  [ERROR] Error processing {plan['path'].name}: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
    
    print()
    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print(f"Successfully processed: {success_count}/{len(lesson_plans)}")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print()
    print(f"Output directory: {output_dir}")
    print(f"Files saved in week folder root")
    print()
    print("NEW FORMAT APPLIED:")
    print("-" * 80)
    print("[OK] Metadata format: '11/17/25 | Wednesday | ELA | Grade 3 | T5'")
    print("[OK] Gray dividing lines between sentence frame areas")
    print("[OK] No line separating metadata from sentence frames")
    print()


if __name__ == "__main__":
    # Default week folder path
    week_folder_path = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47"
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        week_folder_path = sys.argv[1]
    
    generate_sentence_frames_for_week(week_folder_path)


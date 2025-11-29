#!/usr/bin/env python3
"""
Diagnostic script to check why sentence frames HTML/PDF were not generated for W48.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.sentence_frames_pdf_generator import SentenceFramesPDFGenerator
from backend.file_manager import get_file_manager


def check_sentence_frames_in_json(lesson_json: Dict[str, Any]) -> Dict[str, Any]:
    """Check if sentence frames exist in lesson JSON and where they are located."""
    result = {
        "has_frames": False,
        "frames_locations": [],
        "total_frames": 0,
        "day_level_frames": 0,
        "slot_level_frames": 0,
    }
    
    days = lesson_json.get("days", {})
    if not isinstance(days, dict):
        return result
    
    for day_name, day_data in days.items():
        if not isinstance(day_data, dict):
            continue
        
        # Check day-level frames
        day_frames = day_data.get("sentence_frames", [])
        if day_frames and isinstance(day_frames, list) and len(day_frames) > 0:
            result["has_frames"] = True
            result["day_level_frames"] += len(day_frames)
            result["frames_locations"].append(f"{day_name} (day-level): {len(day_frames)} frames")
        
        # Check slot-level frames
        slots = day_data.get("slots", [])
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                slot_frames = slot.get("sentence_frames", [])
                if slot_frames and isinstance(slot_frames, list) and len(slot_frames) > 0:
                    result["has_frames"] = True
                    result["slot_level_frames"] += len(slot_frames)
                    slot_num = slot.get("slot_number", "?")
                    result["frames_locations"].append(
                        f"{day_name} slot {slot_num} (slot-level): {len(slot_frames)} frames"
                    )
    
    result["total_frames"] = result["day_level_frames"] + result["slot_level_frames"]
    return result


def find_lesson_plans_in_folder(folder_path: Path) -> List[Dict[str, Any]]:
    """Find all lesson plan JSON files in the folder."""
    lesson_plans = []
    
    if not folder_path.exists():
        print(f"ERROR: Folder does not exist: {folder_path}")
        return lesson_plans
    
    json_files = list(folder_path.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files in {folder_path}")
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check if it's a lesson plan
            if isinstance(data, dict) and ("metadata" in data or "days" in data):
                # Extract lesson_json if wrapped
                lesson_json = data.get("lesson_json", data)
                
                # Check for sentence frames
                frames_check = check_sentence_frames_in_json(lesson_json)
                
                if frames_check["has_frames"]:
                    metadata = lesson_json.get("metadata", {})
                    lesson_plans.append({
                        "path": json_file,
                        "lesson_json": lesson_json,
                        "week_of": metadata.get("week_of", "Unknown"),
                        "teacher": metadata.get("teacher_name", "Unknown"),
                        "frames_check": frames_check,
                    })
        except Exception as e:
            print(f"  Warning: Could not read {json_file.name}: {e}")
            continue
    
    return lesson_plans


def test_sentence_frames_generation(lesson_json: Dict[str, Any], output_folder: Path) -> Dict[str, Any]:
    """Test sentence frames generation."""
    result = {
        "success": False,
        "error": None,
        "html_path": None,
        "pdf_path": None,
    }
    
    try:
        generator = SentenceFramesPDFGenerator()
        
        # Extract frames to verify they can be extracted
        payloads = generator.extract_sentence_frames(lesson_json)
        
        if not payloads:
            result["error"] = "No sentence frames extracted from lesson JSON"
            return result
        
        print(f"  Extracted {len(payloads)} sentence frame payload(s)")
        
        # Try to generate HTML
        metadata = lesson_json.get("metadata", {})
        teacher_name = metadata.get("teacher_name", "Unknown")
        
        html_filename = f"test_sentence_frames_{metadata.get('week_of', 'unknown')}.html"
        html_path = output_folder / html_filename
        
        try:
            generated_html = generator.generate_html(
                lesson_json,
                str(html_path),
                user_name=teacher_name,
            )
            result["html_path"] = generated_html
            result["success"] = True
            print(f"  [OK] HTML generated: {html_path}")
            
            # Try to generate PDF
            pdf_path = html_path.with_suffix(".pdf")
            try:
                generated_pdf = generator.generate_pdf(
                    lesson_json,
                    str(pdf_path),
                    user_name=teacher_name,
                    keep_html=True,
                )
                result["pdf_path"] = generated_pdf
                print(f"  [OK] PDF generated: {pdf_path}")
            except Exception as pdf_error:
                result["error"] = f"PDF generation failed: {pdf_error}"
                print(f"  [WARN] PDF generation failed: {pdf_error}")
        except Exception as html_error:
            result["error"] = f"HTML generation failed: {html_error}"
            print(f"  [ERROR] HTML generation failed: {html_error}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        result["error"] = f"Generation test failed: {e}"
        print(f"  [ERROR] Generation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def main():
    """Main diagnostic function."""
    print("=" * 80)
    print("SENTENCE FRAMES GENERATION DIAGNOSTIC - W48")
    print("=" * 80)
    print()
    
    # Check the expected folder
    expected_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W48")
    
    print(f"Expected folder: {expected_folder}")
    print(f"Folder exists: {expected_folder.exists()}")
    print()
    
    if not expected_folder.exists():
        print("ERROR: Expected folder does not exist!")
        print("Please verify the path is correct.")
        return
    
    # Find lesson plans
    print("Scanning for lesson plan JSON files...")
    print("-" * 80)
    lesson_plans = find_lesson_plans_in_folder(expected_folder)
    
    if not lesson_plans:
        print("No lesson plans with sentence frames found in the folder.")
        print()
        print("Checking for any JSON files...")
        json_files = list(expected_folder.rglob("*.json"))
        if json_files:
            print(f"Found {len(json_files)} JSON files but none contain sentence frames:")
            for json_file in json_files[:5]:
                print(f"  - {json_file.name}")
        return
    
    print(f"Found {len(lesson_plans)} lesson plan(s) with sentence frames:")
    for i, plan in enumerate(lesson_plans, 1):
        print(f"\n[{i}] {plan['path'].name}")
        print(f"    Week: {plan['week_of']}")
        print(f"    Teacher: {plan['teacher']}")
        print(f"    Sentence Frames Check:")
        print(f"      - Has frames: {plan['frames_check']['has_frames']}")
        print(f"      - Total frames: {plan['frames_check']['total_frames']}")
        print(f"      - Day-level: {plan['frames_check']['day_level_frames']}")
        print(f"      - Slot-level: {plan['frames_check']['slot_level_frames']}")
        print(f"      - Locations: {', '.join(plan['frames_check']['frames_locations'])}")
    
    print()
    print("=" * 80)
    print("TESTING SENTENCE FRAMES GENERATION")
    print("=" * 80)
    print()
    
    # Test generation for each plan
    for i, plan in enumerate(lesson_plans, 1):
        print(f"\n[{i}/{len(lesson_plans)}] Testing: {plan['path'].name}")
        print("-" * 80)
        
        # Check file manager path resolution
        file_mgr = get_file_manager()
        week_folder = file_mgr.get_week_folder(plan['week_of'])
        print(f"File manager week folder: {week_folder}")
        print(f"Expected folder: {expected_folder}")
        print(f"Folders match: {week_folder == expected_folder}")
        
        # Test generation
        result = test_sentence_frames_generation(plan['lesson_json'], expected_folder)
        
        if result["success"]:
            print(f"  [SUCCESS] Generation test passed!")
            if result["html_path"]:
                print(f"    HTML: {result['html_path']}")
            if result["pdf_path"]:
                print(f"    PDF: {result['pdf_path']}")
        else:
            print(f"  [FAILED] Generation test failed: {result['error']}")
    
    print()
    print("=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()


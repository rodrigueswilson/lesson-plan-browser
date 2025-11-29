"""
End-to-end test for media preservation through the full pipeline.
Tests: DOCX parsing -> JSON storage -> DOCX rendering
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer


def test_end_to_end():
    """Test complete pipeline: parse -> store -> render."""
    print("\n" + "=" * 60)
    print("End-to-End Media Preservation Test")
    print("=" * 60)
    
    # Step 1: Parse input with media
    print("\n[1/4] Parsing input DOCX with media...")
    input_path = "tests/fixtures/lesson_with_both.docx"
    
    if not Path(input_path).exists():
        print(f"ERROR: Input file not found: {input_path}")
        return False
    
    parser = DOCXParser(input_path)
    images = parser.extract_images()
    hyperlinks = parser.extract_hyperlinks()
    
    print(f"  Extracted: {len(images)} images, {len(hyperlinks)} hyperlinks")
    
    if not images and not hyperlinks:
        print("  ERROR: No media found in input")
        return False
    
    # Step 2: Create lesson JSON with media
    print("\n[2/4] Creating lesson JSON with media metadata...")
    lesson_json = {
        "metadata": {
            "teacher_name": "Test Teacher",
            "grade": "5",
            "subject": "ELA",
            "week_of": "10/14-10/18",
            "homeroom": "5A"
        },
        "days": {
            "monday": {
                "unit_lesson": "Story Elements",
                "objective": {
                    "content_objective": "Identify story elements",
                    "student_goal": "Students will identify characters, setting, and plot",
                    "wida_objective": "Use academic vocabulary to describe story elements"
                },
                "anticipatory_set": {
                    "original_content": "Review previous story elements lesson",
                    "bilingual_bridge": "Connect to students' native language stories"
                },
                "tailored_instruction": {
                    "original_content": "Interactive story mapping activity",
                    "co_teaching_model": {},
                    "ell_support": [],
                    "special_needs_support": [],
                    "materials": ["Story map worksheet", "Example stories"]
                },
                "misconceptions": {
                    "original_content": "Students may confuse setting with plot",
                    "linguistic_note": {}
                },
                "assessment": {
                    "primary_assessment": "Story map completion",
                    "bilingual_overlay": {}
                },
                "homework": {
                    "original_content": "Read a story and identify elements",
                    "family_connection": "Share story with family"
                }
            },
            "tuesday": {"unit_lesson": "Continue story elements"},
            "wednesday": {"unit_lesson": "Practice with new stories"},
            "thursday": {"unit_lesson": "Assessment preparation"},
            "friday": {"unit_lesson": "Story elements quiz"}
        },
        "_images": images,
        "_hyperlinks": hyperlinks
    }
    
    print(f"  Created JSON with {len(images)} images and {len(hyperlinks)} hyperlinks")
    
    # Step 3: Save JSON (simulate what batch_processor does)
    print("\n[3/4] Saving JSON to file...")
    json_path = "output/test_media_e2e.json"
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(lesson_json, f, indent=2)
    
    print(f"  Saved: {json_path}")
    
    # Verify JSON size
    json_size = Path(json_path).stat().st_size
    print(f"  JSON size: {json_size:,} bytes")
    
    # Step 4: Render to DOCX
    print("\n[4/4] Rendering JSON to output DOCX...")
    template_path = "input/Lesson Plan Template SY'25-26.docx"
    output_path = "output/test_media_e2e.docx"
    
    renderer = DOCXRenderer(template_path)
    success = renderer.render(lesson_json, output_path)
    
    if not success:
        print("  ERROR: Rendering failed")
        return False
    
    print(f"  Rendered: {output_path}")
    
    # Verify output
    if not Path(output_path).exists():
        print("  ERROR: Output file not created")
        return False
    
    output_size = Path(output_path).stat().st_size
    print(f"  Output size: {output_size:,} bytes")
    
    # Verify media in output
    print("\n[Verification] Checking output DOCX...")
    output_parser = DOCXParser(output_path)
    output_images = output_parser.extract_images()
    output_hyperlinks = output_parser.extract_hyperlinks()
    
    print(f"  Found in output: {len(output_images)} images, {len(output_hyperlinks)} hyperlinks")
    
    # Check if media was preserved
    images_preserved = len(output_images) == len(images)
    hyperlinks_preserved = len(output_hyperlinks) == len(hyperlinks)
    
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"  Images preserved: {'YES' if images_preserved else 'NO'} ({len(output_images)}/{len(images)})")
    print(f"  Hyperlinks preserved: {'YES' if hyperlinks_preserved else 'NO'} ({len(output_hyperlinks)}/{len(hyperlinks)})")
    
    if images_preserved and hyperlinks_preserved:
        print("\n  SUCCESS: All media preserved through pipeline!")
        return True
    else:
        print("\n  PARTIAL: Some media may not have been preserved")
        return False


def main():
    """Run end-to-end test."""
    try:
        success = test_end_to_end()
        
        print("\n" + "=" * 60)
        if success:
            print("OVERALL: PASS")
        else:
            print("OVERALL: FAIL")
        print("=" * 60)
        
        return success
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

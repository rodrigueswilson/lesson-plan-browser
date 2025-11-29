"""
Test script for image and hyperlink preservation.
Tests extraction from input DOCX and insertion into output DOCX.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer
from backend.telemetry import logger


def test_image_extraction():
    """Test image extraction from fixture."""
    print("\n=== Testing Image Extraction ===")
    
    fixture_path = "tests/fixtures/lesson_with_image.docx"
    if not Path(fixture_path).exists():
        print(f"SKIP: Fixture not found: {fixture_path}")
        return False
    
    parser = DOCXParser(fixture_path)
    images = parser.extract_images()
    
    print(f"Found {len(images)} images")
    for i, img in enumerate(images, 1):
        print(f"  Image {i}:")
        print(f"    - Filename: {img.get('filename', 'unknown')}")
        print(f"    - Content Type: {img.get('content_type', 'unknown')}")
        print(f"    - Data Size: {len(img.get('data', ''))} bytes (base64)")
    
    return len(images) > 0


def test_hyperlink_extraction():
    """Test hyperlink extraction from fixture."""
    print("\n=== Testing Hyperlink Extraction ===")
    
    fixture_path = "tests/fixtures/lesson_with_hyperlinks.docx"
    if not Path(fixture_path).exists():
        print(f"SKIP: Fixture not found: {fixture_path}")
        return False
    
    parser = DOCXParser(fixture_path)
    hyperlinks = parser.extract_hyperlinks()
    
    print(f"Found {len(hyperlinks)} hyperlinks")
    for i, link in enumerate(hyperlinks, 1):
        print(f"  Link {i}:")
        print(f"    - Text: {link.get('text', 'unknown')}")
        print(f"    - URL: {link.get('url', 'unknown')}")
    
    return len(hyperlinks) > 0


def test_image_insertion():
    """Test image insertion into rendered document."""
    print("\n=== Testing Image Insertion ===")
    
    # Create mock lesson JSON with images
    fixture_path = "tests/fixtures/lesson_with_image.docx"
    if not Path(fixture_path).exists():
        print(f"SKIP: Fixture not found: {fixture_path}")
        return False
    
    # Extract images from fixture
    parser = DOCXParser(fixture_path)
    images = parser.extract_images()
    
    if not images:
        print("SKIP: No images found in fixture")
        return False
    
    # Create minimal lesson JSON
    lesson_json = {
        "metadata": {
            "teacher_name": "Test Teacher",
            "grade": "3",
            "subject": "Math",
            "week_of": "10/14-10/18",
            "homeroom": "3A"
        },
        "days": {
            "monday": {
                "unit_lesson": "Test Lesson",
                "objective": {
                    "content_objective": "Test objective",
                    "student_goal": "Test goal",
                    "wida_objective": "Test WIDA"
                },
                "anticipatory_set": {
                    "original_content": "Test anticipatory set"
                },
                "tailored_instruction": {
                    "original_content": "Test instruction"
                },
                "misconceptions": {
                    "original_content": "Test misconceptions"
                },
                "assessment": {
                    "primary_assessment": "Test assessment"
                },
                "homework": {
                    "original_content": "Test homework"
                }
            },
            "tuesday": {"unit_lesson": "No School"},
            "wednesday": {"unit_lesson": "No School"},
            "thursday": {"unit_lesson": "No School"},
            "friday": {"unit_lesson": "No School"}
        },
        "_images": images  # Add extracted images
    }
    
    # Render to output
    template_path = "input/Lesson Plan Template SY'25-26.docx"
    output_path = "output/test_image_preservation.docx"
    
    renderer = DOCXRenderer(template_path)
    success = renderer.render(lesson_json, output_path)
    
    if success:
        print(f"SUCCESS: Document rendered with {len(images)} images")
        print(f"Output: {output_path}")
        return True
    else:
        print("FAILED: Document rendering failed")
        return False


def test_hyperlink_insertion():
    """Test hyperlink insertion into rendered document."""
    print("\n=== Testing Hyperlink Insertion ===")
    
    # Create mock lesson JSON with hyperlinks
    fixture_path = "tests/fixtures/lesson_with_hyperlinks.docx"
    if not Path(fixture_path).exists():
        print(f"SKIP: Fixture not found: {fixture_path}")
        return False
    
    # Extract hyperlinks from fixture
    parser = DOCXParser(fixture_path)
    hyperlinks = parser.extract_hyperlinks()
    
    if not hyperlinks:
        print("SKIP: No hyperlinks found in fixture")
        return False
    
    # Create minimal lesson JSON
    lesson_json = {
        "metadata": {
            "teacher_name": "Test Teacher",
            "grade": "3",
            "subject": "Science",
            "week_of": "10/14-10/18",
            "homeroom": "3A"
        },
        "days": {
            "monday": {
                "unit_lesson": "Test Lesson",
                "objective": {
                    "content_objective": "Test objective",
                    "student_goal": "Test goal",
                    "wida_objective": "Test WIDA"
                },
                "anticipatory_set": {
                    "original_content": "Test anticipatory set"
                },
                "tailored_instruction": {
                    "original_content": "Test instruction"
                },
                "misconceptions": {
                    "original_content": "Test misconceptions"
                },
                "assessment": {
                    "primary_assessment": "Test assessment"
                },
                "homework": {
                    "original_content": "Test homework"
                }
            },
            "tuesday": {"unit_lesson": "No School"},
            "wednesday": {"unit_lesson": "No School"},
            "thursday": {"unit_lesson": "No School"},
            "friday": {"unit_lesson": "No School"}
        },
        "_hyperlinks": hyperlinks  # Add extracted hyperlinks
    }
    
    # Render to output
    template_path = "input/Lesson Plan Template SY'25-26.docx"
    output_path = "output/test_hyperlink_preservation.docx"
    
    renderer = DOCXRenderer(template_path)
    success = renderer.render(lesson_json, output_path)
    
    if success:
        print(f"SUCCESS: Document rendered with {len(hyperlinks)} hyperlinks")
        print(f"Output: {output_path}")
        return True
    else:
        print("FAILED: Document rendering failed")
        return False


def test_combined_preservation():
    """Test both images and hyperlinks together."""
    print("\n=== Testing Combined Preservation ===")
    
    # Use combined lesson fixture
    fixture_path = "tests/fixtures/lesson_with_both.docx"
    if not Path(fixture_path).exists():
        print(f"SKIP: Fixture not found: {fixture_path}")
        return False
    
    parser = DOCXParser(fixture_path)
    images = parser.extract_images()
    hyperlinks = parser.extract_hyperlinks()
    
    print(f"Found {len(images)} images and {len(hyperlinks)} hyperlinks")
    
    if not images and not hyperlinks:
        print("SKIP: No media found in fixture")
        return False
    
    # Create minimal lesson JSON
    lesson_json = {
        "metadata": {
            "teacher_name": "Test Teacher",
            "grade": "4",
            "subject": "ELA",
            "week_of": "10/14-10/18",
            "homeroom": "4B"
        },
        "days": {
            "monday": {
                "unit_lesson": "Test Lesson",
                "objective": {
                    "content_objective": "Test objective",
                    "student_goal": "Test goal",
                    "wida_objective": "Test WIDA"
                },
                "anticipatory_set": {
                    "original_content": "Test anticipatory set"
                },
                "tailored_instruction": {
                    "original_content": "Test instruction"
                },
                "misconceptions": {
                    "original_content": "Test misconceptions"
                },
                "assessment": {
                    "primary_assessment": "Test assessment"
                },
                "homework": {
                    "original_content": "Test homework"
                }
            },
            "tuesday": {"unit_lesson": "No School"},
            "wednesday": {"unit_lesson": "No School"},
            "thursday": {"unit_lesson": "No School"},
            "friday": {"unit_lesson": "No School"}
        }
    }
    
    # Add media if found
    if images:
        lesson_json["_images"] = images
    if hyperlinks:
        lesson_json["_hyperlinks"] = hyperlinks
    
    # Render to output
    template_path = "input/Lesson Plan Template SY'25-26.docx"
    output_path = "output/test_combined_preservation.docx"
    
    renderer = DOCXRenderer(template_path)
    success = renderer.render(lesson_json, output_path)
    
    if success:
        print(f"SUCCESS: Document rendered with {len(images)} images and {len(hyperlinks)} hyperlinks")
        print(f"Output: {output_path}")
        return True
    else:
        print("FAILED: Document rendering failed")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Media Preservation Test Suite")
    print("=" * 60)
    
    results = {
        "Image Extraction": test_image_extraction(),
        "Hyperlink Extraction": test_hyperlink_extraction(),
        "Image Insertion": test_image_insertion(),
        "Hyperlink Insertion": test_hyperlink_insertion(),
        "Combined Preservation": test_combined_preservation()
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL/SKIP"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

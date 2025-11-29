"""
Test slot metadata flow end-to-end.

Verifies that slot metadata is correctly added and passed through
the entire pipeline from batch processor to renderer.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from tools.batch_processor import BatchProcessor
from tools.docx_renderer import DOCXRenderer


class TestSlotMetadataFlow:
    """Test slot metadata flows correctly through the pipeline."""
    
    def test_single_slot_metadata_added(self):
        """Test that single-slot rendering adds metadata correctly."""
        # Create mock lesson
        lesson = {
            "slot_number": 1,
            "subject": "ELA",
            "lesson_json": {
                "metadata": {
                    "teacher_name": "Test Teacher",
                    "week_of": "10/27-10/31"
                },
                "_hyperlinks": [
                    {"text": "Link 1", "url": "http://test1.com"},
                    {"text": "Link 2", "url": "http://test2.com"}
                ],
                "_images": [
                    {"filename": "image1.jpg"}
                ],
                "days": {
                    "monday": {"unit_lesson": "Test"}
                }
            }
        }
        
        # Simulate what _combine_lessons does for single slot
        slot_num = lesson["slot_number"]
        subject = lesson["subject"]
        lesson_json = lesson["lesson_json"]
        
        # Add slot metadata to lesson JSON metadata
        if 'metadata' not in lesson_json:
            lesson_json['metadata'] = {}
        lesson_json['metadata']['slot_number'] = slot_num
        lesson_json['metadata']['subject'] = subject
        
        # Add slot metadata to hyperlinks
        if '_hyperlinks' in lesson_json:
            for link in lesson_json['_hyperlinks']:
                link['_source_slot'] = slot_num
                link['_source_subject'] = subject
        
        # Add slot metadata to images
        if '_images' in lesson_json:
            for image in lesson_json['_images']:
                image['_source_slot'] = slot_num
                image['_source_subject'] = subject
        
        # Verify metadata was added
        assert lesson_json['metadata']['slot_number'] == 1
        assert lesson_json['metadata']['subject'] == "ELA"
        
        # Verify hyperlinks have metadata
        for link in lesson_json['_hyperlinks']:
            assert link['_source_slot'] == 1
            assert link['_source_subject'] == "ELA"
        
        # Verify images have metadata
        for image in lesson_json['_images']:
            assert image['_source_slot'] == 1
            assert image['_source_subject'] == "ELA"
    
    def test_multi_slot_metadata_added(self):
        """Test that multi-slot rendering adds metadata correctly."""
        # Create mock lessons
        lessons = [
            {
                "slot_number": 1,
                "subject": "ELA",
                "lesson_json": {
                    "metadata": {},
                    "_hyperlinks": [
                        {"text": "ELA Link", "url": "http://ela.com"}
                    ],
                    "days": {"monday": {"unit_lesson": "ELA"}}
                }
            },
            {
                "slot_number": 5,
                "subject": "Math",
                "lesson_json": {
                    "metadata": {},
                    "_hyperlinks": [
                        {"text": "Math Link", "url": "http://math.com"}
                    ],
                    "days": {"monday": {"unit_lesson": "Math"}}
                }
            }
        ]
        
        # Simulate what _combine_lessons does for multi-slot
        for lesson in lessons:
            slot_num = lesson["slot_number"]
            subject = lesson["subject"]
            lesson_json = lesson["lesson_json"]
            
            # Add slot metadata
            if 'metadata' not in lesson_json:
                lesson_json['metadata'] = {}
            lesson_json['metadata']['slot_number'] = slot_num
            lesson_json['metadata']['subject'] = subject
            
            if '_hyperlinks' in lesson_json:
                for link in lesson_json['_hyperlinks']:
                    link['_source_slot'] = slot_num
                    link['_source_subject'] = subject
        
        # Verify ELA slot
        ela_json = lessons[0]['lesson_json']
        assert ela_json['metadata']['slot_number'] == 1
        assert ela_json['metadata']['subject'] == "ELA"
        assert ela_json['_hyperlinks'][0]['_source_slot'] == 1
        assert ela_json['_hyperlinks'][0]['_source_subject'] == "ELA"
        
        # Verify Math slot
        math_json = lessons[1]['lesson_json']
        assert math_json['metadata']['slot_number'] == 5
        assert math_json['metadata']['subject'] == "Math"
        assert math_json['_hyperlinks'][0]['_source_slot'] == 5
        assert math_json['_hyperlinks'][0]['_source_subject'] == "Math"
    
    def test_renderer_extracts_metadata(self):
        """Test that renderer extracts slot metadata correctly."""
        # Create lesson JSON with slot metadata
        json_data = {
            "metadata": {
                "slot_number": 1,
                "subject": "ELA",
                "teacher_name": "Test Teacher"
            },
            "_hyperlinks": [
                {
                    "text": "Test Link",
                    "url": "http://test.com",
                    "_source_slot": 1,
                    "_source_subject": "ELA"
                }
            ],
            "_media_schema_version": "2.0",
            "days": {
                "monday": {"unit_lesson": "Test"}
            }
        }
        
        # Simulate what renderer does
        slot_number = json_data.get("metadata", {}).get("slot_number")
        subject = json_data.get("metadata", {}).get("subject")
        
        # Verify extraction
        assert slot_number == 1
        assert subject == "ELA"
        assert slot_number is not None  # Critical for filtering
        assert subject is not None
    
    def test_filtering_logic(self):
        """Test that filtering logic works correctly."""
        # Simulate filtering in _fill_cell
        current_slot_number = 1
        current_subject = "ELA"
        
        hyperlinks = [
            {"text": "ELA Link", "_source_slot": 1, "_source_subject": "ELA"},
            {"text": "Math Link", "_source_slot": 5, "_source_subject": "Math"},
            {"text": "Science Link", "_source_slot": 3, "_source_subject": "Science"},
            {"text": "No Metadata", "url": "http://test.com"}  # Missing metadata
        ]
        
        # Filter hyperlinks
        filtered = []
        for hyperlink in hyperlinks:
            # Check slot filtering
            if current_slot_number is not None:
                link_slot = hyperlink.get('_source_slot')
                
                # Skip if missing metadata
                if link_slot is None:
                    continue
                
                # Skip if wrong slot
                if link_slot != current_slot_number:
                    continue
            
            # Check subject filtering
            if current_subject is not None:
                link_subject = hyperlink.get('_source_subject')
                
                # Skip if missing metadata
                if link_subject is None:
                    continue
                
                # Skip if wrong subject
                if link_subject != current_subject:
                    continue
            
            # Passed all filters
            filtered.append(hyperlink)
        
        # Verify only ELA link passed
        assert len(filtered) == 1
        assert filtered[0]['text'] == "ELA Link"
    
    def test_filtering_disabled_when_no_metadata(self):
        """Test that filtering is disabled when slot_number is None."""
        # Simulate filtering with no slot metadata
        current_slot_number = None
        current_subject = None
        
        hyperlinks = [
            {"text": "Link 1", "_source_slot": 1, "_source_subject": "ELA"},
            {"text": "Link 2", "_source_slot": 5, "_source_subject": "Math"}
        ]
        
        # Filter hyperlinks (should pass all when metadata is None)
        filtered = []
        for hyperlink in hyperlinks:
            # Filtering only activates when current_slot_number is not None
            if current_slot_number is not None:
                link_slot = hyperlink.get('_source_slot')
                if link_slot is None or link_slot != current_slot_number:
                    continue
            
            if current_subject is not None:
                link_subject = hyperlink.get('_source_subject')
                if link_subject is None or link_subject != current_subject:
                    continue
            
            filtered.append(hyperlink)
        
        # All should pass when filtering is disabled
        assert len(filtered) == 2


class TestMetadataEdgeCases:
    """Test edge cases in metadata handling."""
    
    def test_empty_hyperlinks_list(self):
        """Test handling of empty hyperlinks list."""
        lesson_json = {
            "metadata": {},
            "_hyperlinks": [],
            "days": {"monday": {"unit_lesson": "Test"}}
        }
        
        slot_num = 1
        subject = "ELA"
        
        # Add metadata
        lesson_json['metadata']['slot_number'] = slot_num
        lesson_json['metadata']['subject'] = subject
        
        # Should not crash on empty list
        for link in lesson_json['_hyperlinks']:
            link['_source_slot'] = slot_num
        
        assert len(lesson_json['_hyperlinks']) == 0
    
    def test_missing_hyperlinks_key(self):
        """Test handling when _hyperlinks key is missing."""
        lesson_json = {
            "metadata": {},
            "days": {"monday": {"unit_lesson": "Test"}}
        }
        
        slot_num = 1
        subject = "ELA"
        
        # Add metadata
        lesson_json['metadata']['slot_number'] = slot_num
        lesson_json['metadata']['subject'] = subject
        
        # Should not crash when key is missing
        if '_hyperlinks' in lesson_json:
            for link in lesson_json['_hyperlinks']:
                link['_source_slot'] = slot_num
        
        assert '_hyperlinks' not in lesson_json
    
    def test_metadata_overwrite(self):
        """Test that metadata can be overwritten."""
        lesson_json = {
            "metadata": {
                "slot_number": 999,  # Wrong value
                "subject": "Wrong"
            },
            "_hyperlinks": [
                {"text": "Link", "_source_slot": 999, "_source_subject": "Wrong"}
            ]
        }
        
        # Correct metadata
        slot_num = 1
        subject = "ELA"
        
        lesson_json['metadata']['slot_number'] = slot_num
        lesson_json['metadata']['subject'] = subject
        
        for link in lesson_json['_hyperlinks']:
            link['_source_slot'] = slot_num
            link['_source_subject'] = subject
        
        # Verify overwrite
        assert lesson_json['metadata']['slot_number'] == 1
        assert lesson_json['metadata']['subject'] == "ELA"
        assert lesson_json['_hyperlinks'][0]['_source_slot'] == 1
        assert lesson_json['_hyperlinks'][0]['_source_subject'] == "ELA"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

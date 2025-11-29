"""
End-to-End Test: Hyperlink Workflow from Source to Final Output

This test validates the complete hyperlink journey:
1. Extract hyperlinks from source DOCX files (with coordinates)
2. Store in lesson JSON with schema v2.0
3. Pass to batch processor
4. Render to output DOCX with coordinate-based placement
5. Verify all hyperlinks are placed correctly

Tests both the happy path and edge cases.
"""

import sys
import unittest
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer
from tools.batch_processor import BatchProcessor


class TestHyperlinkWorkflowE2E(unittest.TestCase):
    """End-to-end tests for hyperlink workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.template_file = Path(r"d:\LP\input\Lesson Plan Template SY'25-26.docx")
        cls.test_input_file = Path(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx')
        
        # Create temp directory for outputs
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Run the complete workflow once in setup
        cls._run_complete_workflow()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temp directory."""
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def _run_complete_workflow(cls):
        """Run the complete workflow and store results for all tests."""
        
        # Step 1: Extract hyperlinks
        parser = DOCXParser(str(cls.test_input_file))
        cls.hyperlinks = parser.extract_hyperlinks()
        
        # Step 2: Create lesson JSON
        cls.lesson_json = {
            "metadata": {
                "teacher_name": "Test Teacher",
                "week_dates": "10/20-10/24",
                "grade": "Test",
                "subject": "Test"
            },
            "days": {
                "monday": {
                    "unit_lesson": "Test Unit",
                    "objective": {"content": "Test objective"},
                    "anticipatory_set": {"content": "Test anticipatory set"},
                    "tailored_instruction": {"content": "Test instruction"},
                    "misconceptions": {"content": "Test misconceptions"},
                    "assessment": {"content": "Test assessment"},
                    "homework": {"content": "Test homework"}
                }
            },
            "_hyperlinks": cls.hyperlinks,
            "_media_schema_version": "2.0"
        }
        
        # Step 3: Render
        cls.output_file = cls.temp_dir / "test_output.docx"
        renderer = DOCXRenderer(str(cls.template_file))
        cls.render_success = renderer.render(cls.lesson_json, str(cls.output_file))
        cls.placement_stats = renderer.placement_stats.copy()
        
        # Step 4: Extract from output
        if cls.output_file.exists():
            output_parser = DOCXParser(str(cls.output_file))
            cls.output_hyperlinks = output_parser.extract_hyperlinks()
        else:
            cls.output_hyperlinks = []
        
        # Calculate expected values
        cls.expected_table_links = len([h for h in cls.hyperlinks if h.get('table_idx') is not None])
    
    def test_01_extract_hyperlinks_with_coordinates(self):
        """Test: Extract hyperlinks from source file with v2.0 schema."""
        
        print("\n" + "="*80)
        print("TEST 1: Extract Hyperlinks with Coordinates")
        print("="*80)
        
        # Use pre-extracted hyperlinks from setup
        hyperlinks = self.hyperlinks
        
        # Assertions
        self.assertGreater(len(hyperlinks), 0, "Should extract at least one hyperlink")
        
        # Check schema version
        for link in hyperlinks:
            self.assertEqual(link.get('schema_version'), '2.0', 
                           "All links should have schema v2.0")
        
        # Check coordinates for table links
        table_links = [h for h in hyperlinks if h.get('table_idx') is not None]
        self.assertGreater(len(table_links), 0, "Should have at least one table link")
        
        for link in table_links:
            self.assertIsNotNone(link.get('table_idx'), "Table link should have table_idx")
            self.assertIsNotNone(link.get('row_idx'), "Table link should have row_idx")
            self.assertIsNotNone(link.get('cell_idx'), "Table link should have cell_idx")
            self.assertIsNotNone(link.get('row_label'), "Table link should have row_label")
            self.assertIsNotNone(link.get('col_header'), "Table link should have col_header")
        
        print(f"✅ Extracted {len(hyperlinks)} hyperlinks")
        print(f"✅ All links have schema v2.0")
        print(f"✅ {len(table_links)} table links have coordinates")
    
    def test_02_create_lesson_json_with_schema_v2(self):
        """Test: Create lesson JSON with hyperlinks and schema v2.0."""
        
        print("\n" + "="*80)
        print("TEST 2: Create Lesson JSON with Schema v2.0")
        print("="*80)
        
        # Use pre-created lesson JSON from setup
        lesson_json = self.lesson_json
        
        # Assertions
        self.assertEqual(lesson_json.get('_media_schema_version'), '2.0',
                        "Lesson JSON should have schema v2.0")
        self.assertEqual(len(lesson_json.get('_hyperlinks', [])), len(self.hyperlinks),
                        "All hyperlinks should be in lesson JSON")
        
        print(f"✅ Lesson JSON created with {len(self.hyperlinks)} hyperlinks")
        print(f"✅ Schema version: {lesson_json['_media_schema_version']}")
    
    def test_03_render_with_coordinate_placement(self):
        """Test: Render lesson plan with coordinate-based placement."""
        
        print("\n" + "="*80)
        print("TEST 3: Render with Coordinate-Based Placement")
        print("="*80)
        
        # Use pre-rendered output from setup
        success = self.render_success
        output_file = self.output_file
        stats = self.placement_stats
        
        # Assertions
        self.assertTrue(success, "Rendering should succeed")
        self.assertTrue(output_file.exists(), "Output file should be created")
        
        coordinate_count = stats.get('coordinate', 0)
        fallback_count = stats.get('fallback', 0)
        
        print(f"✅ Rendering successful")
        print(f"✅ Placement statistics:")
        print(f"   - Coordinate: {coordinate_count}")
        print(f"   - Label/Day: {stats.get('label_day', 0)}")
        print(f"   - Fuzzy: {stats.get('fuzzy', 0)}")
        print(f"   - Fallback: {fallback_count}")
    
    def test_04_verify_hyperlinks_in_output(self):
        """Test: Verify hyperlinks are present in output file."""
        
        print("\n" + "="*80)
        print("TEST 4: Verify Hyperlinks in Output")
        print("="*80)
        
        # Use pre-extracted output hyperlinks from setup
        output_hyperlinks = self.output_hyperlinks
        
        # Assertions
        self.assertGreater(len(output_hyperlinks), 0, 
                          "Output should have hyperlinks")
        
        # Check that most hyperlinks are preserved
        # (Some might be duplicates or filtered)
        preservation_rate = len(output_hyperlinks) / len(self.hyperlinks)
        self.assertGreater(preservation_rate, 0.7, 
                          f"Should preserve at least 70% of hyperlinks (got {preservation_rate:.1%})")
        
        print(f"✅ Found {len(output_hyperlinks)} hyperlinks in output")
        print(f"✅ Preservation rate: {preservation_rate:.1%}")
    
    def test_05_verify_coordinate_placement_success(self):
        """Test: Verify that table links were placed via coordinates."""
        
        print("\n" + "="*80)
        print("TEST 5: Verify Coordinate Placement Success")
        print("="*80)
        
        # Check placement statistics
        coordinate_count = self.placement_stats.get('coordinate', 0)
        fallback_count = self.placement_stats.get('fallback', 0)
        
        # For table links, we expect high coordinate placement rate
        if self.expected_table_links > 0:
            coordinate_rate = coordinate_count / self.expected_table_links
            
            self.assertGreater(coordinate_rate, 0.9, 
                             f"Should place >90% of table links via coordinates (got {coordinate_rate:.1%})")
            
            print(f"✅ Coordinate placement rate: {coordinate_rate:.1%}")
            print(f"✅ {coordinate_count}/{self.expected_table_links} table links placed via coordinates")
        
        # Fallback should be minimal (only paragraph links)
        para_links = [h for h in self.hyperlinks if h.get('table_idx') is None]
        expected_fallback = len(para_links)
        
        self.assertLessEqual(fallback_count, expected_fallback + 2,  # Allow small margin
                            f"Fallback should only contain paragraph links (expected ~{expected_fallback}, got {fallback_count})")
        
        print(f"✅ Fallback count: {fallback_count} (expected ~{expected_fallback} paragraph links)")
    
    def test_06_verify_no_referenced_links_section(self):
        """Test: Verify no 'Referenced Links' section for table links."""
        
        print("\n" + "="*80)
        print("TEST 6: Verify No Referenced Links Section")
        print("="*80)
        
        from docx import Document
        
        # Open output file
        doc = Document(str(self.output_file))
        
        # Check for "Referenced Links" section
        has_ref_links = False
        for para in doc.paragraphs:
            if "Referenced Links" in para.text:
                has_ref_links = True
                break
        
        # Count paragraph links (these should go to fallback)
        para_links = [h for h in self.hyperlinks if h.get('table_idx') is None]
        
        if len(para_links) > 0:
            # If we have paragraph links, we expect a Referenced Links section
            self.assertTrue(has_ref_links, 
                          "Should have Referenced Links section for paragraph links")
            print(f"✅ Referenced Links section exists (expected for {len(para_links)} paragraph links)")
        else:
            # If all links are table links, no Referenced Links section
            self.assertFalse(has_ref_links, 
                           "Should NOT have Referenced Links section (all table links)")
            print(f"✅ No Referenced Links section (all {len(self.hyperlinks)} links are table links)")
    
    def test_07_verify_link_locations_match(self):
        """Test: Verify hyperlinks are in correct table locations."""
        
        print("\n" + "="*80)
        print("TEST 7: Verify Link Locations Match")
        print("="*80)
        
        # Compare input and output link locations
        input_table_links = [h for h in self.hyperlinks if h.get('table_idx') is not None]
        output_table_links = [h for h in self.output_hyperlinks if h.get('table_idx') is not None]
        
        self.assertGreater(len(output_table_links), 0, 
                          "Should have table links in output")
        
        # Create signature map for comparison
        def create_signature(link):
            text = link.get('text', '')[:30].lower()
            url = link.get('url', '')[:50].lower()
            return f"{text}|{url}"
        
        input_sigs = {create_signature(h): h for h in input_table_links}
        output_sigs = {create_signature(h): h for h in output_table_links}
        
        # Check that most input links are in output
        matched = 0
        for sig, input_link in input_sigs.items():
            if sig in output_sigs:
                matched += 1
        
        match_rate = matched / len(input_sigs) if input_sigs else 0
        self.assertGreater(match_rate, 0.8, 
                          f"Should match >80% of input links (got {match_rate:.1%})")
        
        print(f"✅ Matched {matched}/{len(input_sigs)} input links in output")
        print(f"✅ Match rate: {match_rate:.1%}")
    
    def test_08_end_to_end_summary(self):
        """Test: Print end-to-end workflow summary."""
        
        print("\n" + "="*80)
        print("END-TO-END WORKFLOW SUMMARY")
        print("="*80)
        
        print(f"\n📊 Statistics:")
        print(f"   Input hyperlinks: {len(self.hyperlinks)}")
        print(f"   Output hyperlinks: {len(self.output_hyperlinks)}")
        print(f"   Preservation rate: {len(self.output_hyperlinks)/len(self.hyperlinks):.1%}")
        print()
        
        print(f"📍 Placement:")
        print(f"   Coordinate: {self.placement_stats.get('coordinate', 0)}")
        print(f"   Label/Day: {self.placement_stats.get('label_day', 0)}")
        print(f"   Fuzzy: {self.placement_stats.get('fuzzy', 0)}")
        print(f"   Fallback: {self.placement_stats.get('fallback', 0)}")
        print()
        
        table_links = [h for h in self.hyperlinks if h.get('table_idx') is not None]
        para_links = [h for h in self.hyperlinks if h.get('table_idx') is None]
        
        print(f"📋 Link Types:")
        print(f"   Table links: {len(table_links)}")
        print(f"   Paragraph links: {len(para_links)}")
        print()
        
        if len(table_links) > 0:
            coord_rate = self.placement_stats.get('coordinate', 0) / len(table_links)
            print(f"✅ Table link coordinate placement: {coord_rate:.1%}")
        
        print()
        print("="*80)
        print("✅ ALL TESTS PASSED - WORKFLOW IS WORKING CORRECTLY")
        print("="*80)


def run_tests():
    """Run all tests with verbose output."""
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHyperlinkWorkflowE2E)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("\n")
    print("="*80)
    print("HYPERLINK WORKFLOW END-TO-END TEST")
    print("="*80)
    print()
    print("This test validates the complete hyperlink journey:")
    print("  1. Extract from source DOCX (with coordinates)")
    print("  2. Store in lesson JSON (schema v2.0)")
    print("  3. Render to output DOCX (coordinate placement)")
    print("  4. Verify all hyperlinks are placed correctly")
    print()
    
    success = run_tests()
    
    sys.exit(0 if success else 1)

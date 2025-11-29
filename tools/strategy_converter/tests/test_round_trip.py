"""
Automated round-trip tests for strategy conversion.
Tests JSON→MD→JSON conversion using fixtures from strategies_pack_v2.
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
from schema_validator import SchemaValidator


class RoundTripTester:
    """Automated round-trip conversion tester."""
    
    def __init__(self):
        """Initialize with converters and validator."""
        self.json_to_md = JsonToMarkdownConverter()
        self.md_to_json = MarkdownToJsonConverter()
        self.validator = SchemaValidator()
        self.results = []
    
    def test_strategy(self, strategy: dict, strategy_id: str) -> Tuple[bool, List[str]]:
        """
        Test round-trip conversion for a single strategy.
        
        Args:
            strategy: Original strategy dict
            strategy_id: Strategy identifier for reporting
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        try:
            # Step 1: JSON → Markdown
            md_content = self.json_to_md.convert_strategy(strategy)
            
            # Step 2: Markdown → JSON
            reconstructed = self.md_to_json.parse_strategy(md_content)
            
            # Step 3: Validate reconstructed JSON
            is_valid, validation_errors = self.validator.validate_strategy(reconstructed)
            if not is_valid:
                errors.append(f"Validation failed: {validation_errors}")
            
            # Step 4: Compare critical fields
            critical_fields = [
                'id', 'strategy_name', 'evidence_tier', 'core_principle',
                'high_level_categories', 'primary_skill', 'skill_weights',
                'delivery_modes', 'l1_modes', 'is_integrated_framework'
            ]
            
            for field in critical_fields:
                original_value = strategy.get(field)
                reconstructed_value = reconstructed.get(field)
                
                if original_value != reconstructed_value:
                    errors.append(
                        f"Field '{field}' mismatch:\n"
                        f"  Original: {original_value}\n"
                        f"  Reconstructed: {reconstructed_value}"
                    )
            
            # Step 5: Compare arrays (order-independent for some fields)
            array_fields = ['applicable_contexts', 'implementation_steps', 'primary_benefits']
            for field in array_fields:
                original = strategy.get(field, [])
                reconstructed_arr = reconstructed.get(field, [])
                
                if len(original) != len(reconstructed_arr):
                    errors.append(
                        f"Array '{field}' length mismatch: "
                        f"{len(original)} vs {len(reconstructed_arr)}"
                    )
            
            # Step 6: Check definitions if present
            if 'definitions' in strategy:
                if 'definitions' not in reconstructed:
                    errors.append("Definitions section lost in conversion")
                else:
                    orig_defs = strategy['definitions']
                    recon_defs = reconstructed['definitions']
                    
                    for key in ['short_en', 'long_en', 'look_fors', 'non_examples']:
                        if key in orig_defs and key not in recon_defs:
                            errors.append(f"Definition field '{key}' lost in conversion")
            
            success = len(errors) == 0
            return success, errors
            
        except Exception as e:
            return False, [f"Exception during conversion: {str(e)}"]
    
    def test_category_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        Test round-trip conversion for an entire category file.
        
        Args:
            file_path: Path to category JSON file
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Step 1: JSON → Markdown
            md_content = self.json_to_md.convert_category_file(original_data)
            
            # Step 2: Markdown → JSON
            reconstructed_data = self.md_to_json.parse_category_file(md_content)
            
            # Step 3: Validate reconstructed JSON
            is_valid, validation_errors = self.validator.validate_category_file(reconstructed_data)
            if not is_valid:
                errors.append(f"Category validation failed: {validation_errors}")
            
            # Step 4: Check metadata
            orig_meta = original_data.get('_meta', {})
            recon_meta = reconstructed_data.get('_meta', {})
            
            for key in ['category', 'schema_version', 'strategy_count']:
                if orig_meta.get(key) != recon_meta.get(key):
                    errors.append(
                        f"Metadata '{key}' mismatch: "
                        f"{orig_meta.get(key)} vs {recon_meta.get(key)}"
                    )
            
            # Step 5: Check strategy count
            orig_count = len(original_data.get('strategies', []))
            recon_count = len(reconstructed_data.get('strategies', []))
            
            if orig_count != recon_count:
                errors.append(
                    f"Strategy count mismatch: {orig_count} vs {recon_count}"
                )
            
            # Step 6: Test each strategy
            for idx, orig_strategy in enumerate(original_data.get('strategies', [])):
                if idx < len(reconstructed_data.get('strategies', [])):
                    recon_strategy = reconstructed_data['strategies'][idx]
                    strategy_id = orig_strategy.get('id', f'strategy_{idx}')
                    
                    success, strategy_errors = self.test_strategy(orig_strategy, strategy_id)
                    if not success:
                        errors.append(f"Strategy '{strategy_id}' failed:")
                        errors.extend(f"  {err}" for err in strategy_errors)
            
            success = len(errors) == 0
            return success, errors
            
        except Exception as e:
            return False, [f"Exception during file conversion: {str(e)}"]
    
    def run_all_tests(self, strategies_pack_dir: Path) -> int:
        """
        Run tests on all category files in strategies_pack_v2.
        
        Args:
            strategies_pack_dir: Path to strategies_pack_v2 directory
            
        Returns:
            Number of failed tests
        """
        print("=" * 70)
        print("ROUND-TRIP CONVERSION TEST SUITE")
        print("=" * 70)
        print()
        
        # Find all category JSON files
        core_dir = strategies_pack_dir / 'core'
        specialized_dir = strategies_pack_dir / 'specialized'
        
        test_files = []
        if core_dir.exists():
            test_files.extend(core_dir.glob('*.json'))
        if specialized_dir.exists():
            test_files.extend(specialized_dir.glob('*.json'))
        
        if not test_files:
            print(f"No test files found in {strategies_pack_dir}")
            return 1
        
        print(f"Found {len(test_files)} category files to test\n")
        
        failed_count = 0
        
        for file_path in sorted(test_files):
            print(f"Testing: {file_path.name}")
            print("-" * 70)
            
            success, errors = self.test_category_file(file_path)
            
            if success:
                print("PASSED - Round-trip conversion successful")
                self.results.append((file_path.name, True, []))
            else:
                print("FAILED - Round-trip conversion errors:")
                for error in errors:
                    print(f"  {error}")
                self.results.append((file_path.name, False, errors))
                failed_count += 1
            
            print()
        
        # Summary
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total files tested: {len(test_files)}")
        print(f"Passed: {len(test_files) - failed_count}")
        print(f"Failed: {failed_count}")
        print()
        
        if failed_count > 0:
            print("Failed files:")
            for name, success, errors in self.results:
                if not success:
                    print(f"  - {name}")
        
        return failed_count


def main():
    """Main test entry point."""
    # Locate strategies_pack_v2 directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    strategies_pack_dir = project_root / 'strategies_pack_v2'
    
    if not strategies_pack_dir.exists():
        print(f"Error: strategies_pack_v2 not found at {strategies_pack_dir}")
        return 1
    
    tester = RoundTripTester()
    failed_count = tester.run_all_tests(strategies_pack_dir)
    
    return 0 if failed_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

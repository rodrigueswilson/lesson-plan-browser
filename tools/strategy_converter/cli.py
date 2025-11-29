"""
Command-line interface for strategy conversion.
Supports JSON↔MD conversion with validation and dry-run modes.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional
import difflib

from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
from schema_validator import SchemaValidator


class ConverterCLI:
    """Command-line interface for strategy conversion."""
    
    def __init__(self):
        """Initialize CLI with converters and validator."""
        self.json_to_md = JsonToMarkdownConverter()
        self.md_to_json = MarkdownToJsonConverter()
        self.validator = SchemaValidator()
    
    def convert(self, input_path: str, output_path: Optional[str] = None,
                validate: bool = True, dry_run: bool = False, 
                show_diff: bool = False) -> int:
        """
        Convert between JSON and Markdown formats.
        
        Args:
            input_path: Input file path
            output_path: Output file path (auto-generated if None)
            validate: Whether to validate output against schema
            dry_run: If True, don't write files, just show what would happen
            show_diff: Show diff between input and output (for round-trip testing)
            
        Returns:
            Exit code (0 = success, 1 = error)
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            return 1
        
        # Determine conversion direction
        input_ext = input_file.suffix.lower()
        
        if input_ext == '.json':
            return self._convert_json_to_md(input_file, output_path, validate, dry_run, show_diff)
        elif input_ext == '.md':
            return self._convert_md_to_json(input_file, output_path, validate, dry_run, show_diff)
        else:
            print(f"Error: Unsupported file extension: {input_ext}", file=sys.stderr)
            print("Supported: .json, .md", file=sys.stderr)
            return 1
    
    def _convert_json_to_md(self, input_file: Path, output_path: Optional[str],
                            validate: bool, dry_run: bool, show_diff: bool) -> int:
        """Convert JSON to Markdown."""
        print(f"Converting JSON to Markdown: {input_file}")
        
        # Validate input JSON first
        if validate:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if '_meta' in data:
                is_valid, errors = self.validator.validate_category_file(data)
            else:
                is_valid, errors = self.validator.validate_strategy(data)
            
            if not is_valid:
                print("Input JSON validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"  {error}", file=sys.stderr)
                return 1
            
            print("Input JSON validation: PASSED")
        
        # Generate output path
        if output_path is None:
            output_path = input_file.with_suffix('.md')
        
        # Convert
        try:
            if dry_run:
                markdown_content = self.json_to_md.convert_file(str(input_file), output_path=None)
                print(f"\nDry run - would write to: {output_path}")
                print(f"Output size: {len(markdown_content)} characters")
                print("\nPreview (first 500 chars):")
                print(markdown_content[:500])
            else:
                markdown_content = self.json_to_md.convert_file(str(input_file), str(output_path))
                print(f"Successfully wrote: {output_path}")
                print(f"Output size: {len(markdown_content)} characters")
            
            return 0
            
        except Exception as e:
            print(f"Conversion error: {e}", file=sys.stderr)
            return 1
    
    def _convert_md_to_json(self, input_file: Path, output_path: Optional[str],
                           validate: bool, dry_run: bool, show_diff: bool) -> int:
        """Convert Markdown to JSON."""
        print(f"Converting Markdown to JSON: {input_file}")
        
        # Generate output path
        if output_path is None:
            output_path = input_file.with_suffix('.json')
        
        # Convert
        try:
            if dry_run:
                markdown_content = input_file.read_text(encoding='utf-8')
                
                if '**Category:**' in markdown_content:
                    data = self.md_to_json.parse_category_file(markdown_content)
                else:
                    data = self.md_to_json.parse_strategy(markdown_content)
                
                print(f"\nDry run - would write to: {output_path}")
                print(f"Parsed {len(data.get('strategies', [data]))} strategy/strategies")
                
                if validate:
                    if '_meta' in data:
                        is_valid, errors = self.validator.validate_category_file(data)
                    else:
                        is_valid, errors = self.validator.validate_strategy(data)
                    
                    if is_valid:
                        print("Output JSON validation: PASSED")
                    else:
                        print("Output JSON validation: FAILED", file=sys.stderr)
                        for error in errors:
                            print(f"  {error}", file=sys.stderr)
                        return 1
                
                print("\nPreview (formatted JSON):")
                print(json.dumps(data, indent=2)[:500])
                
            else:
                data = self.md_to_json.convert_file(str(input_file), str(output_path))
                
                if validate:
                    if '_meta' in data:
                        is_valid, errors = self.validator.validate_category_file(data)
                    else:
                        is_valid, errors = self.validator.validate_strategy(data)
                    
                    if is_valid:
                        print("Output JSON validation: PASSED")
                    else:
                        print("Output JSON validation: FAILED", file=sys.stderr)
                        for error in errors:
                            print(f"  {error}", file=sys.stderr)
                        return 1
                
                print(f"Successfully wrote: {output_path}")
                print(f"Parsed {len(data.get('strategies', [data]))} strategy/strategies")
            
            return 0
            
        except Exception as e:
            print(f"Conversion error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    def round_trip_test(self, input_path: str, show_diff: bool = True) -> int:
        """
        Test round-trip conversion (JSON→MD→JSON or MD→JSON→MD).
        
        Args:
            input_path: Input file path
            show_diff: Show differences if any
            
        Returns:
            Exit code (0 = success, 1 = error)
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            return 1
        
        print(f"Round-trip testing: {input_file}")
        
        input_ext = input_file.suffix.lower()
        
        try:
            if input_ext == '.json':
                # JSON → MD → JSON
                print("Step 1: JSON → Markdown")
                md_content = self.json_to_md.convert_file(str(input_file), output_path=None)
                
                print("Step 2: Markdown → JSON")
                if '**Category:**' in md_content:
                    final_data = self.md_to_json.parse_category_file(md_content)
                else:
                    final_data = self.md_to_json.parse_strategy(md_content)
                
                # Compare
                with open(input_file, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                
                original_json = json.dumps(original_data, indent=2, sort_keys=True)
                final_json = json.dumps(final_data, indent=2, sort_keys=True)
                
            else:  # .md
                # MD → JSON → MD
                print("Step 1: Markdown → JSON")
                json_data = self.md_to_json.convert_file(str(input_file), output_path=None)
                
                print("Step 2: JSON → Markdown")
                if '_meta' in json_data:
                    final_md = self.json_to_md.convert_category_file(json_data, output_path=None)
                else:
                    final_md = self.json_to_md.convert_strategy(json_data)
                
                # Compare
                original_md = input_file.read_text(encoding='utf-8')
                
                # Normalize whitespace for comparison
                original_json = original_md.strip()
                final_json = final_md.strip()
            
            # Check if identical
            if original_json == final_json:
                print("\nRound-trip test: PASSED (100% fidelity)")
                return 0
            else:
                print("\nRound-trip test: FAILED (data changed)", file=sys.stderr)
                
                if show_diff:
                    print("\nDifferences:")
                    diff = difflib.unified_diff(
                        original_json.splitlines(keepends=True),
                        final_json.splitlines(keepends=True),
                        fromfile='original',
                        tofile='round-trip',
                        lineterm=''
                    )
                    print(''.join(diff))
                
                return 1
                
        except Exception as e:
            print(f"Round-trip test error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert bilingual teaching strategies between JSON and Markdown formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert JSON to Markdown
  python cli.py convert input.json -o output.md
  
  # Convert Markdown to JSON with validation
  python cli.py convert input.md --validate
  
  # Dry run (preview without writing)
  python cli.py convert input.json --check
  
  # Round-trip test
  python cli.py test input.json --diff
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between JSON and Markdown')
    convert_parser.add_argument('input', help='Input file path (.json or .md)')
    convert_parser.add_argument('-o', '--output', help='Output file path (auto-generated if omitted)')
    convert_parser.add_argument('--validate', action='store_true', help='Validate against schema')
    convert_parser.add_argument('--check', '--dry-run', action='store_true', 
                               dest='dry_run', help='Dry run - show what would happen without writing files')
    convert_parser.add_argument('--diff', action='store_true', help='Show diff (for round-trip comparison)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run round-trip conversion test')
    test_parser.add_argument('input', help='Input file path (.json or .md)')
    test_parser.add_argument('--diff', action='store_true', help='Show differences if test fails')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = ConverterCLI()
    
    if args.command == 'convert':
        return cli.convert(
            args.input,
            args.output,
            validate=args.validate,
            dry_run=args.dry_run,
            show_diff=args.diff
        )
    elif args.command == 'test':
        return cli.round_trip_test(args.input, show_diff=args.diff)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

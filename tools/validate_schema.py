"""
JSON Schema Validator
Validates lesson plan JSON files against the schema.
"""

import json
import sys
from pathlib import Path
from typing import Tuple, List

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("Error: jsonschema package not installed")
    print("Install with: pip install jsonschema")
    sys.exit(1)


def load_schema(schema_path: Path) -> dict:
    """
    Load JSON schema from file.
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Schema dictionary
    """
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_json_file(json_path: Path) -> dict:
    """
    Load JSON file.
    
    Args:
        json_path: Path to JSON file
        
    Returns:
        JSON dictionary
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_json(data: dict, schema: dict) -> Tuple[bool, List[str]]:
    """
    Validate JSON data against schema.
    
    Args:
        data: JSON data to validate
        schema: JSON schema
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = Draft7Validator(schema)
    errors = []
    
    for error in validator.iter_errors(data):
        # Format error message
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        message = f"Error at '{path}': {error.message}"
        
        # Add context if available
        if error.validator_value:
            message += f" (expected: {error.validator_value})"
        
        errors.append(message)
    
    return len(errors) == 0, errors


def validate_file(json_path: Path, schema_path: Path, verbose: bool = False) -> bool:
    """
    Validate a JSON file against schema.
    
    Args:
        json_path: Path to JSON file
        schema_path: Path to schema file
        verbose: Print detailed output
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Load schema
        if verbose:
            print(f"Loading schema: {schema_path}")
        schema = load_schema(schema_path)
        
        # Load JSON
        if verbose:
            print(f"Loading JSON: {json_path}")
        data = load_json_file(json_path)
        
        # Validate
        if verbose:
            print("Validating...")
        is_valid, errors = validate_json(data, schema)
        
        if is_valid:
            print(f"✓ VALID: {json_path.name}")
            return True
        else:
            print(f"✗ INVALID: {json_path.name}")
            print(f"  Found {len(errors)} error(s):")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"✗ JSON PARSE ERROR: {json_path.name}")
        print(f"  {str(e)}")
        return False
    except FileNotFoundError as e:
        print(f"✗ FILE NOT FOUND: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False


def validate_directory(directory: Path, schema_path: Path, pattern: str = "*.json") -> Tuple[int, int]:
    """
    Validate all JSON files in a directory.
    
    Args:
        directory: Directory containing JSON files
        schema_path: Path to schema file
        pattern: File pattern to match
        
    Returns:
        Tuple of (valid_count, total_count)
    """
    json_files = list(directory.glob(pattern))
    
    if not json_files:
        print(f"No JSON files found in {directory}")
        return 0, 0
    
    print(f"Validating {len(json_files)} file(s) in {directory}")
    print("=" * 60)
    
    valid_count = 0
    for json_file in json_files:
        if validate_file(json_file, schema_path):
            valid_count += 1
        print()
    
    return valid_count, len(json_files)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate lesson plan JSON files against schema'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='JSON file or directory to validate'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        default=Path('schemas/lesson_output_schema.json'),
        help='Path to JSON schema file'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--pattern',
        default='*.json',
        help='File pattern for directory validation (default: *.json)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    input_path = args.input.resolve()
    schema_path = args.schema.resolve()
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    if not input_path.exists():
        print(f"Error: Input not found: {input_path}")
        sys.exit(1)
    
    # Validate
    if input_path.is_file():
        # Single file
        success = validate_file(input_path, schema_path, args.verbose)
        sys.exit(0 if success else 1)
    elif input_path.is_dir():
        # Directory
        valid_count, total_count = validate_directory(
            input_path,
            schema_path,
            args.pattern
        )
        
        print("=" * 60)
        print(f"Results: {valid_count}/{total_count} valid")
        
        if valid_count == total_count:
            print("✓ All files valid!")
            sys.exit(0)
        else:
            print(f"✗ {total_count - valid_count} file(s) invalid")
            sys.exit(1)
    else:
        print(f"Error: Input must be a file or directory: {input_path}")
        sys.exit(1)


if __name__ == '__main__':
    main()

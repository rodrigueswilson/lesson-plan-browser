"""
Lesson Plan Renderer
Validates JSON against schema and renders to markdown using Jinja2 templates.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

try:
    import jsonschema
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
except ImportError:
    print("Error: Required packages not installed")
    print("Install with: pip install jsonschema jinja2")
    sys.exit(1)


class LessonPlanRenderer:
    """Validates and renders lesson plans from JSON to markdown."""
    
    def __init__(self, schema_path: Path, template_dir: Path):
        """
        Initialize renderer.
        
        Args:
            schema_path: Path to JSON schema file
            template_dir: Path to Jinja2 templates directory
        """
        self.schema_path = schema_path
        self.template_dir = template_dir
        
        # Load schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            autoescape=False  # We're generating markdown, not HTML
        )
    
    def validate(self, data: Dict) -> Tuple[bool, list]:
        """
        Validate lesson plan JSON against schema.
        
        Args:
            data: Lesson plan data as dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            jsonschema.validate(data, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            # Collect validation errors
            errors = []
            
            # Main error message
            errors.append(str(e.message))
            
            # Add path context
            if e.path:
                path = '.'.join(str(p) for p in e.path)
                errors.append(f"Error at: {path}")
            
            # Add expected value
            if e.validator_value:
                errors.append(f"Expected: {e.validator_value}")
            
            return False, errors
        except jsonschema.SchemaError as e:
            return False, [f"Schema error: {str(e)}"]
    
    def render(self, data: Dict, output_path: Optional[Path] = None) -> str:
        """
        Render lesson plan from JSON data to markdown.
        
        Args:
            data: Validated lesson plan data
            output_path: Optional path to write output file
            
        Returns:
            Rendered markdown string
        """
        try:
            template = self.env.get_template('lesson_plan.md.jinja2')
            output = template.render(**data)
            
            # Write to file if path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output)
            
            return output
            
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Template not found: {e}")
        except Exception as e:
            raise RuntimeError(f"Rendering error: {str(e)}")
    
    def render_from_file(self, json_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Load JSON file, validate, and render.
        
        Args:
            json_path: Path to JSON input file
            output_path: Path to markdown output file
            
        Returns:
            Tuple of (success, message)
        """
        # Load JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except FileNotFoundError:
            return False, f"File not found: {json_path}"
        
        # Validate
        valid, errors = self.validate(data)
        if not valid:
            error_msg = "Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            return False, error_msg
        
        # Render
        try:
            self.render(data, output_path)
            return True, f"Successfully rendered to {output_path}"
        except Exception as e:
            return False, f"Rendering failed: {str(e)}"


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Render lesson plan from JSON to markdown')
    parser.add_argument('input', type=Path, help='Input JSON file')
    parser.add_argument('output', type=Path, help='Output markdown file')
    parser.add_argument('--schema', type=Path, 
                       default=Path('schemas/lesson_output_schema.json'),
                       help='JSON schema file (default: schemas/lesson_output_schema.json)')
    parser.add_argument('--templates', type=Path,
                       default=Path('templates'),
                       help='Templates directory (default: templates)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate, do not render')
    
    args = parser.parse_args()
    
    # Check schema exists
    if not args.schema.exists():
        print(f"Error: Schema file not found: {args.schema}")
        sys.exit(1)
    
    # Check templates directory exists
    if not args.templates.exists():
        print(f"Error: Templates directory not found: {args.templates}")
        sys.exit(1)
    
    # Initialize renderer
    try:
        renderer = LessonPlanRenderer(args.schema, args.templates)
    except Exception as e:
        print(f"Error initializing renderer: {e}")
        sys.exit(1)
    
    # Load and validate
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}")
        print(f"  {str(e)}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Validate
    valid, errors = renderer.validate(data)
    
    if not valid:
        print(f"✗ Validation failed for {args.input.name}")
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print(f"✓ Validation passed for {args.input.name}")
    
    # If validate-only, exit here
    if args.validate_only:
        sys.exit(0)
    
    # Render
    try:
        output = renderer.render(data, args.output)
        print(f"✓ Successfully rendered to {args.output}")
        print(f"  Output size: {len(output)} characters")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Rendering failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

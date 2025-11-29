"""
Schema validation for bilingual teaching strategies.
Validates against v1.7_enhanced schema definition.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator


class SchemaValidator:
    """Validates strategy data against v1.7_enhanced schema."""
    
    def __init__(self, schema_path: str = None):
        """
        Initialize validator with schema file.
        
        Args:
            schema_path: Path to schema JSON file (defaults to bundled schema)
        """
        if schema_path is None:
            schema_path = Path(__file__).parent / 'schema' / 'v1_7_enhanced.json'
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)
        
        # Create resolver for $ref references
        from jsonschema import RefResolver
        self.resolver = RefResolver.from_schema(self.schema)
        self.validator = Draft7Validator(self.schema, resolver=self.resolver)
    
    def validate_strategy(self, strategy: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a single strategy object.
        
        Args:
            strategy: Strategy dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate against schema with resolver for $ref
            strategy_schema = self.schema['definitions']['strategy']
            validator = Draft7Validator(strategy_schema, resolver=self.resolver)
            validator.validate(strategy)
            
            # Additional custom validations
            custom_errors = self._custom_validations(strategy)
            errors.extend(custom_errors)
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            # Add path information for nested errors
            if e.path:
                path_str = '.'.join(str(p) for p in e.path)
                errors.append(f"  at path: {path_str}")
        
        return len(errors) == 0, errors
    
    def validate_category_file(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a complete category file with metadata and strategies.
        
        Args:
            data: Category file dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate against category_file schema with resolver for $ref
            category_schema = self.schema['definitions']['category_file']
            validator = Draft7Validator(category_schema, resolver=self.resolver)
            validator.validate(data)
            
            # Validate strategy count matches
            declared_count = data.get('_meta', {}).get('strategy_count', 0)
            actual_count = len(data.get('strategies', []))
            
            if declared_count != actual_count:
                errors.append(
                    f"Strategy count mismatch: _meta declares {declared_count} "
                    f"but found {actual_count} strategies"
                )
            
            # Validate each strategy
            for idx, strategy in enumerate(data.get('strategies', [])):
                is_valid, strategy_errors = self.validate_strategy(strategy)
                if not is_valid:
                    errors.append(f"Strategy #{idx + 1} ('{strategy.get('id', 'unknown')}'):")
                    errors.extend(f"  {err}" for err in strategy_errors)
            
        except ValidationError as e:
            errors.append(f"Category file validation error: {e.message}")
        
        return len(errors) == 0, errors
    
    def _custom_validations(self, strategy: Dict) -> List[str]:
        """
        Perform custom validation rules beyond JSON schema.
        
        Args:
            strategy: Strategy dictionary
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Validate skill_weights sum to ~1.0 or 0.0
        weights = strategy.get('skill_weights', {})
        if weights:
            total = sum(weights.values())
            # Allow slightly more tolerance for floating point rounding (0.05 instead of 0.01)
            if not (abs(total - 1.0) <= 0.05 or abs(total) <= 0.01):
                errors.append(
                    f"skill_weights sum to {total:.2f}, expected ~1.0 or 0.0. "
                    f"Weights: {weights}"
                )
        
        # Validate cross_refs point to valid IDs (if we have context)
        cross_refs = strategy.get('cross_refs', [])
        if cross_refs:
            for ref in cross_refs:
                if not isinstance(ref, str) or not ref:
                    errors.append(f"Invalid cross_ref: '{ref}' (must be non-empty string)")
        
        # Validate primary_skill consistency with skill_weights
        primary_skill = strategy.get('primary_skill')
        if primary_skill and primary_skill != 'integrated' and weights:
            primary_weight = weights.get(primary_skill, 0.0)
            if primary_weight == 0.0:
                errors.append(
                    f"primary_skill '{primary_skill}' has 0.0 weight in skill_weights"
                )
        
        # Validate secondary_skills don't include primary_skill
        secondary_skills = strategy.get('secondary_skills', [])
        if primary_skill and primary_skill in secondary_skills:
            errors.append(
                f"primary_skill '{primary_skill}' should not appear in secondary_skills"
            )
        
        # Validate definitions structure if present
        definitions = strategy.get('definitions', {})
        if definitions:
            if 'look_fors' in definitions and not isinstance(definitions['look_fors'], list):
                errors.append("definitions.look_fors must be an array")
            if 'non_examples' in definitions and not isinstance(definitions['non_examples'], list):
                errors.append("definitions.non_examples must be an array")
        
        return errors
    
    def get_schema_version(self) -> str:
        """Get the schema version."""
        return self.schema.get('version', 'unknown')
    
    def list_required_fields(self, object_type: str = 'strategy') -> List[str]:
        """
        List required fields for a given object type.
        
        Args:
            object_type: 'strategy' or 'category_file'
            
        Returns:
            List of required field names
        """
        if object_type in self.schema['definitions']:
            return self.schema['definitions'][object_type].get('required', [])
        return []
    
    def get_field_enum_values(self, field_path: str) -> List[Any]:
        """
        Get allowed enum values for a field.
        
        Args:
            field_path: Dot-separated path like 'evidence_tier' or 'skill_weights.speaking'
            
        Returns:
            List of allowed values, or empty list if not an enum
        """
        # Navigate schema to find field definition
        parts = field_path.split('.')
        current = self.schema['definitions']['strategy']['properties']
        
        for part in parts:
            if part in current:
                current = current[part]
                if 'properties' in current:
                    current = current['properties']
            else:
                return []
        
        return current.get('enum', [])

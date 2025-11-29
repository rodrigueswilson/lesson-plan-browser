"""Quick test script for converter functionality."""

import json
import sys
from pathlib import Path

from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
from schema_validator import SchemaValidator

def test_single_strategy():
    """Test conversion with a single strategy."""
    
    # Load a strategy from language_skills.json
    strategies_file = Path(r'd:\LP\strategies_pack_v2\core\language_skills.json')
    
    with open(strategies_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get first strategy
    strategy = data['strategies'][0]
    print(f"Testing strategy: {strategy['id']}")
    print("=" * 70)
    
    # Step 1: Validate original
    validator = SchemaValidator()
    is_valid, errors = validator.validate_strategy(strategy)
    print(f"\n1. Original validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"   {err}")
    
    # Step 2: Convert to Markdown
    converter_j2m = JsonToMarkdownConverter()
    md_content = converter_j2m.convert_strategy(strategy)
    print(f"\n2. JSON → Markdown: {len(md_content)} characters")
    print("\nMarkdown preview (first 500 chars):")
    print(md_content[:500])
    
    # Step 3: Convert back to JSON
    converter_m2j = MarkdownToJsonConverter()
    reconstructed = converter_m2j.parse_strategy(md_content)
    print(f"\n3. Markdown → JSON: Reconstructed strategy '{reconstructed.get('id', 'unknown')}'")
    
    # Step 4: Validate reconstructed
    is_valid, errors = validator.validate_strategy(reconstructed)
    print(f"\n4. Reconstructed validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"   {err}")
    
    # Step 5: Compare key fields
    print("\n5. Field comparison:")
    fields_to_check = ['id', 'strategy_name', 'primary_skill', 'evidence_tier']
    all_match = True
    
    for field in fields_to_check:
        orig = strategy.get(field)
        recon = reconstructed.get(field)
        match = orig == recon
        all_match = all_match and match
        status = "✓" if match else "✗"
        print(f"   {status} {field}: {orig} == {recon}")
    
    # Check skill_weights
    orig_weights = strategy.get('skill_weights', {})
    recon_weights = reconstructed.get('skill_weights', {})
    weights_match = orig_weights == recon_weights
    all_match = all_match and weights_match
    status = "✓" if weights_match else "✗"
    print(f"   {status} skill_weights: {orig_weights} == {recon_weights}")
    
    print("\n" + "=" * 70)
    print(f"OVERALL: {'SUCCESS - Round-trip conversion works!' if all_match else 'FAILED - Data mismatch'}")
    
    return 0 if all_match else 1

if __name__ == '__main__':
    sys.exit(test_single_strategy())

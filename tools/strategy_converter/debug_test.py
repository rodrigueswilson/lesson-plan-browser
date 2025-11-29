"""Debug script to see actual test errors."""

import json
from pathlib import Path
from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
from schema_validator import SchemaValidator

# Test one file
file_path = Path('d:/LP/strategies_pack_v2/core/language_skills.json')

print(f"Testing: {file_path.name}")
print("=" * 70)

try:
    # Load original
    with open(file_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"Loaded {len(original_data.get('strategies', []))} strategies")
    
    # Convert to MD
    j2m = JsonToMarkdownConverter()
    md_content = j2m.convert_category_file(original_data)
    print(f"Converted to Markdown: {len(md_content)} chars")
    
    # Convert back to JSON
    m2j = MarkdownToJsonConverter()
    reconstructed_data = m2j.parse_category_file(md_content)
    print(f"Parsed back: {len(reconstructed_data.get('strategies', []))} strategies")
    
    # Validate
    validator = SchemaValidator()
    is_valid, errors = validator.validate_category_file(reconstructed_data)
    
    print(f"\nValidation: {'PASSED' if is_valid else 'FAILED'}")
    
    if not is_valid:
        print("\nErrors:")
        for i, error in enumerate(errors[:20]):  # First 20 errors
            print(f"{i+1}. {error}")
    
    # Compare strategy counts
    orig_count = len(original_data.get('strategies', []))
    recon_count = len(reconstructed_data.get('strategies', []))
    
    if orig_count != recon_count:
        print(f"\nSTRATEGY COUNT MISMATCH: {orig_count} vs {recon_count}")
    
    # Check first strategy
    if original_data.get('strategies') and reconstructed_data.get('strategies'):
        orig_first = original_data['strategies'][0]
        recon_first = reconstructed_data['strategies'][0]
        
        print(f"\nFirst strategy comparison:")
        print(f"  Original ID: {orig_first.get('id')}")
        print(f"  Reconstructed ID: {recon_first.get('id')}")
        
        # Check a few key fields
        for field in ['strategy_name', 'primary_skill', 'evidence_tier']:
            orig_val = orig_first.get(field)
            recon_val = recon_first.get(field)
            match = "OK" if orig_val == recon_val else "MISMATCH"
            print(f"  {field}: {match}")
            if orig_val != recon_val:
                print(f"    Original: {orig_val}")
                print(f"    Reconstructed: {recon_val}")
        
        # Check skill_weights specifically
        orig_weights = orig_first.get('skill_weights', {})
        recon_weights = recon_first.get('skill_weights', {})
        print(f"\nSkill weights comparison:")
        print(f"  Original: {orig_weights} (sum={sum(orig_weights.values()):.2f})")
        print(f"  Reconstructed: {recon_weights} (sum={sum(recon_weights.values()):.2f})")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

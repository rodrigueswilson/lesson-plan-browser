# Strategy Converter - Usage Examples

## Installation

```bash
cd d:\LP\tools\strategy_converter
pip install -r requirements.txt
```

## Basic Conversions

### Example 1: Convert Single Category File (JSON → Markdown)

```bash
python cli.py convert d:\LP\strategies_pack_v2\core\language_skills.json
```

Output: `language_skills.md` in the same directory

### Example 2: Convert with Custom Output Path

```bash
python cli.py convert d:\LP\strategies_pack_v2\core\language_skills.json -o d:\LP\docs\language_skills_readable.md
```

### Example 3: Convert Markdown Back to JSON

```bash
python cli.py convert d:\LP\docs\language_skills_readable.md -o d:\LP\strategies_pack_v2\core\language_skills_updated.json --validate
```

## Dry-Run Mode (Preview Without Writing)

### Example 4: Preview Conversion

```bash
python cli.py convert d:\LP\strategies_pack_v2\core\frameworks_models.json --check
```

Output shows what would be created without writing files:
```
Converting JSON to Markdown: d:\LP\strategies_pack_v2\core\frameworks_models.json
Input JSON validation: PASSED

Dry run - would write to: d:\LP\strategies_pack_v2\core\frameworks_models.md
Output size: 15234 characters

Preview (first 500 chars):
# Frameworks Models Strategies

**Category:** frameworks_models
**Description:** Comprehensive pedagogical frameworks and instructional models
...
```

## Validation

### Example 5: Validate During Conversion

```bash
python cli.py convert input.md -o output.json --validate
```

If validation fails, you'll see detailed errors:
```
Output JSON validation: FAILED
  Schema validation error: 'skill_weights' is a required property
    at path: strategies.2
  Strategy 'siop' failed:
    skill_weights sum to 0.75, expected ~1.0 or 0.0. Weights: {'speaking': 0.25, 'listening': 0.25, 'reading': 0.25, 'writing': 0.0}
```

## Round-Trip Testing

### Example 6: Test Data Fidelity

```bash
python cli.py test d:\LP\strategies_pack_v2\core\cross_linguistic.json --diff
```

Output shows if conversion preserves all data:
```
Round-trip testing: d:\LP\strategies_pack_v2\core\cross_linguistic.json
Step 1: JSON → Markdown
Step 2: Markdown → JSON

Round-trip test: PASSED (100% fidelity)
```

### Example 7: Test with Diff on Failure

```bash
python cli.py test problematic_file.json --diff
```

If test fails, shows exact differences:
```
Round-trip test: FAILED (data changed)

Differences:
--- original
+++ round-trip
@@ -15,7 +15,7 @@
   "primary_skill": "reading",
-  "secondary_skills": ["writing", "speaking"],
+  "secondary_skills": ["writing"],
```

## Workflow: Update Strategy in Markdown

### Example 8: Complete Edit Workflow

```bash
# Step 1: Convert to Markdown for editing
python cli.py convert d:\LP\strategies_pack_v2\core\language_skills.json

# Step 2: Edit language_skills.md in your text editor
# (Make changes to strategy descriptions, add new strategies, etc.)

# Step 3: Convert back to JSON with validation
python cli.py convert d:\LP\strategies_pack_v2\core\language_skills.md --validate

# Step 4: Verify round-trip integrity
python cli.py test d:\LP\strategies_pack_v2\core\language_skills.json --diff
```

## Batch Operations

### Example 9: Convert All Core Strategies

PowerShell:
```powershell
Get-ChildItem d:\LP\strategies_pack_v2\core\*.json | ForEach-Object {
    python cli.py convert $_.FullName --validate
}
```

Bash:
```bash
for file in d:/LP/strategies_pack_v2/core/*.json; do
    python cli.py convert "$file" --validate
done
```

### Example 10: Test All Categories

```bash
python tests\test_round_trip.py
```

Output:
```
======================================================================
ROUND-TRIP CONVERSION TEST SUITE
======================================================================

Found 6 category files to test

Testing: assessment_scaffolding.json
----------------------------------------------------------------------
✓ PASSED - Round-trip conversion successful

Testing: cross_linguistic.json
----------------------------------------------------------------------
✓ PASSED - Round-trip conversion successful

...

======================================================================
TEST SUMMARY
======================================================================
Total files tested: 6
Passed: 6
Failed: 0
```

## Advanced Use Cases

### Example 11: Quick Test Script

```python
from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
import json

# Load strategy
with open('strategy.json', 'r') as f:
    strategy = json.load(f)

# Convert to Markdown
converter = JsonToMarkdownConverter()
md_content = converter.convert_strategy(strategy)

# Save to file
with open('strategy.md', 'w', encoding='utf-8') as f:
    f.write(md_content)
```

### Example 12: Programmatic Validation

```python
from schema_validator import SchemaValidator

validator = SchemaValidator()

# Validate strategy
is_valid, errors = validator.validate_strategy(strategy_dict)

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")

# Get allowed values for a field
evidence_tiers = validator.get_field_enum_values('evidence_tier')
print(f"Allowed evidence tiers: {evidence_tiers}")
# Output: ['research-backed', 'practice-based/mixed', 'emerging']
```

### Example 13: Custom Conversion Pipeline

```python
from pathlib import Path
from json_to_md import JsonToMarkdownConverter
from md_to_json import MarkdownToJsonConverter
from schema_validator import SchemaValidator

def convert_and_validate(json_path, md_path):
    """Convert JSON to MD and validate round-trip."""
    
    # Convert to Markdown
    j2m = JsonToMarkdownConverter()
    md_content = j2m.convert_file(json_path, md_path)
    
    # Convert back to JSON
    m2j = MarkdownToJsonConverter()
    temp_json = md_path.replace('.md', '_temp.json')
    reconstructed = m2j.convert_file(md_path, temp_json)
    
    # Validate
    validator = SchemaValidator()
    is_valid, errors = validator.validate_category_file(reconstructed)
    
    if is_valid:
        print(f"✓ {json_path} → {md_path} (validated)")
        Path(temp_json).unlink()  # Clean up temp file
        return True
    else:
        print(f"✗ Validation failed for {md_path}")
        for error in errors:
            print(f"  {error}")
        return False

# Use it
convert_and_validate(
    'd:/LP/strategies_pack_v2/core/language_skills.json',
    'd:/LP/docs/language_skills.md'
)
```

## Troubleshooting

### Issue: Skill Weights Don't Sum to 1.0

**Error:**
```
skill_weights sum to 0.85, expected ~1.0 or 0.0
```

**Fix in Markdown:**
```markdown
**Skill Weights:** speaking: 0.25; listening: 0.25; reading: 0.25; writing: 0.25
```

### Issue: Missing Required Field

**Error:**
```
'high_level_categories' is a required property
```

**Fix in Markdown:**
```markdown
**High-Level Categories:** Language Skill Development, Cross-Linguistic & Biliteracy
```

### Issue: Invalid Enum Value

**Error:**
```
'advanced' is not one of ['research-backed', 'practice-based/mixed', 'emerging']
```

**Fix in Markdown:**
```markdown
**Evidence Tier:** research-backed
```

### Issue: Round-Trip Test Shows Whitespace Differences

This is usually harmless. The converter normalizes whitespace. If critical data is preserved, the conversion is successful.

## Integration with Lesson Plan Builder

The converter integrates with the main application:

1. **Strategy Updates**: Edit strategies in Markdown, convert to JSON for use in FastAPI backend
2. **Documentation**: Generate human-readable docs from JSON for teacher reference
3. **Version Control**: Markdown is easier to diff in Git than JSON
4. **Validation**: Ensure all strategies meet schema requirements before deployment

### Example: Pre-Deployment Validation

```bash
# Validate all strategies before building app
python tests\test_round_trip.py

# If all pass, strategies are ready for production
# If any fail, fix issues in Markdown and re-convert
```

## Tips

1. **Always validate** after converting Markdown → JSON to catch errors early
2. **Use dry-run** to preview changes before committing
3. **Run round-trip tests** to ensure data integrity
4. **Keep backups** of original JSON files before batch operations
5. **Check diffs** when round-trip tests fail to identify exact issues

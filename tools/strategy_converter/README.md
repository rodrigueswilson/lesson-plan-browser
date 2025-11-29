# Strategy Converter

Bidirectional JSON↔Markdown converter for bilingual teaching strategies with schema validation and round-trip testing.

## Features

- **Bidirectional Conversion**: JSON → Markdown and Markdown → JSON
- **Schema Validation**: Validates against v1.7_enhanced schema
- **Round-Trip Testing**: Automated tests ensure 100% data fidelity
- **Sentinel-Based Parsing**: Robust extraction using unique heading markers
- **Dry-Run Mode**: Preview changes without writing files
- **Diff Support**: Compare original and converted files

## Installation

```bash
cd d:\LP\tools\strategy_converter
pip install -r requirements.txt
```

## Quick Start

### Convert JSON to Markdown

```bash
python cli.py convert input.json -o output.md
```

### Convert Markdown to JSON

```bash
python cli.py convert input.md -o output.json --validate
```

### Dry Run (Preview Only)

```bash
python cli.py convert input.json --check
```

### Round-Trip Test

```bash
python cli.py test input.json --diff
```

## Architecture

```
strategy_converter/
├── schema/
│   └── v1_7_enhanced.json      # Canonical schema definition
├── tests/
│   └── test_round_trip.py      # Automated test suite
├── __init__.py                 # Package exports
├── utils.py                    # Shared utilities
├── schema_validator.py         # Schema validation
├── json_to_md.py              # JSON → MD converter
├── md_to_json.py              # MD → JSON converter
└── cli.py                     # Command-line interface
```

## Schema v1.7_enhanced Support

The converter fully supports all v1.7_enhanced fields:

### Core Fields
- `id`, `strategy_name`, `aliases`, `present_in`
- `evidence_tier`, `core_principle`
- `applicable_contexts`, `implementation_steps`, `primary_benefits`
- `research_foundation`, `cross_refs`

### v1.6+ Enhanced Fields
- `high_level_categories[]` - Multiple categories (array)
- `skill_weights{}` - Numeric weights for each skill
- `delivery_modes[]` - Implementation contexts
- `l1_modes[]` - L1 usage patterns

### v1.7+ Definitions
- `definitions.short_en` - Brief definition
- `definitions.long_en` - Detailed explanation
- `definitions.look_fors[]` - Observable indicators
- `definitions.non_examples[]` - Common misapplications

## Sentinel-Based Parsing

Each section uses unique sentinel headings for robust extraction:

```markdown
### Strategy ID: bilingual_dictionary

**Name:** Bilingual Dictionary and Glossary Use

**Aliases:** Bilingual glossaries

**Evidence Tier:** practice-based/mixed

**High-Level Categories:** Language Skill Development, Cross-Linguistic & Biliteracy

**Primary Skill:** reading

**Secondary Skills:** writing

**Skill Weights:** speaking: 0.0; listening: 0.0; reading: 0.5; writing: 0.5

**Delivery Mode:** push-in, small-group, whole-group

**L1 Mode:** translanguaging, preview-review

**Core Principle:**
Leverage L1–L2 dictionaries to clarify new terms and support independent comprehension.

**Applicable Contexts:**
- Self-directed reading or research
- Content lessons with dense academic vocabulary
- Writing tasks requiring precise word choice

**Implementation Steps:**
1. Model context-first inference, then confirm with a bilingual dictionary.
2. Embed routine look-ups in reading/writing; teach efficient dictionary skills.
3. Verify fit-in-context (e.g., reverse-translation or image check).

**Primary Benefits:**
- Improves comprehension of academic texts
- Builds bilingual vocabulary and learner autonomy

**Research Foundation:** Jim Cummins, Ellen Bialystok

**Cross-References:** explicit_vocabulary, cognate_awareness

**Short Definition:**
Strategic use of bilingual dictionaries and glossaries to support vocabulary development and reading comprehension.

**Long Definition:**
Bilingual Dictionary and Glossary Use involves teaching students to strategically leverage L1–L2 dictionaries...

**Look-Fors (Observable Indicators):**
- Students attempting context clues before dictionary consultation
- Efficient dictionary navigation and multiple definition consideration

**Non-Examples (Avoid):**
- Immediate dictionary dependence without context consideration
- Using only monolingual English dictionaries with beginning learners

---
```

## Shared Utilities

The `utils.py` module provides reusable functions:

- `normalize_array()` - Convert strings/lists to normalized arrays
- `format_skill_weights()` - Format weights as readable string
- `parse_skill_weights()` - Parse weights string to dict
- `format_list_as_bullets()` - Convert list to Markdown bullets
- `parse_bullet_list()` - Extract items from bullet list
- `extract_sentinel_section()` - Extract content between sentinels
- `sanitize_id()` - Convert text to snake_case ID
- `validate_skill_weights()` - Ensure weights sum to ~1.0

## Validation Rules

The schema validator enforces:

1. **Required Fields**: All v1.7 required fields must be present
2. **Enum Values**: Fields like `evidence_tier`, `primary_skill` must use valid values
3. **Skill Weights**: Must sum to ~1.0 (or 0.0 for none)
4. **Primary/Secondary Consistency**: Primary skill shouldn't appear in secondary
5. **Array Types**: Proper array structure for lists
6. **Definitions Structure**: Correct nested object format

## CLI Usage

### Convert Command

```bash
python cli.py convert <input> [options]

Options:
  -o, --output PATH    Output file path (auto-generated if omitted)
  --validate          Validate against schema
  --check, --dry-run  Preview without writing files
  --diff              Show diff for comparison
```

### Test Command

```bash
python cli.py test <input> [options]

Options:
  --diff              Show differences if test fails
```

## Running Tests

### Automated Test Suite

```bash
cd tests
python test_round_trip.py
```

This tests all category files in `strategies_pack_v2/`:
- `core/language_skills.json` (9 strategies)
- `core/frameworks_models.json` (7 strategies)
- `core/cross_linguistic.json` (8 strategies)
- `core/assessment_scaffolding.json` (5 strategies)
- `specialized/social_interactive.json` (2 strategies)
- `specialized/cultural_identity.json` (2 strategies)

### Manual Testing

Test a specific file:

```bash
python cli.py test d:\LP\strategies_pack_v2\core\language_skills.json --diff
```

## Workflow Integration

### Update Strategy in Markdown

1. Convert JSON to Markdown:
   ```bash
   python cli.py convert strategies.json -o strategies.md
   ```

2. Edit `strategies.md` in your preferred editor

3. Convert back to JSON with validation:
   ```bash
   python cli.py convert strategies.md --validate
   ```

4. Run round-trip test to verify:
   ```bash
   python cli.py test strategies.json --diff
   ```

### Batch Conversion

Convert all category files:

```bash
for file in d:\LP\strategies_pack_v2\core\*.json; do
    python cli.py convert "$file" --validate
done
```

## Error Handling

The converter provides detailed error messages:

- **Schema Validation Errors**: Shows field path and expected values
- **Parsing Errors**: Indicates which sentinel/section failed
- **Round-Trip Failures**: Displays diff showing exact changes
- **File Errors**: Clear messages for missing files or permissions

## Performance

- **Speed**: ~0.1s per strategy (33 strategies in <4s)
- **Memory**: Streams files, minimal memory footprint
- **Accuracy**: 100% round-trip fidelity when properly formatted

## Maintenance

### Updating Schema

1. Edit `schema/v1_7_enhanced.json`
2. Update `SENTINELS` in `json_to_md.py` and `md_to_json.py` if adding fields
3. Add parsing logic in converters
4. Update `utils.py` if new data types needed
5. Run test suite to verify

### Adding New Fields

1. Add to schema with proper type/constraints
2. Add sentinel marker to both converters
3. Implement formatting in `json_to_md.py`
4. Implement parsing in `md_to_json.py`
5. Add validation logic if needed
6. Update tests

## Troubleshooting

### Round-Trip Test Fails

- Check for extra whitespace in Markdown
- Verify sentinel headings match exactly
- Ensure skill_weights sum to 1.0
- Check array formatting (bullets vs numbered lists)

### Validation Errors

- Review required fields in schema
- Check enum values match allowed list
- Verify nested object structure
- Ensure arrays contain correct types

### Parsing Errors

- Confirm sentinel markers are present
- Check for malformed Markdown (missing bullets, etc.)
- Verify section ordering matches expected format
- Look for special characters breaking regex

## License

Part of the Bilingual Weekly Plan Builder project.

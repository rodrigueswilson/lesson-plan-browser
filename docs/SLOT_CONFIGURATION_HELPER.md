# Slot Configuration Helper Tool

**Date:** 2025-12-13  
**Status:** ✅ Complete

## Overview

A comprehensive tool to help users configure their slot settings by analyzing document structures and suggesting optimal configurations. The tool can suggest configurations, validate existing ones, and generate configuration JSON files.

## Features

1. **Suggest Configuration:** Analyze documents and suggest slot configurations
2. **Validate Configuration:** Compare existing configuration with document structures
3. **Generate JSON:** Create configuration JSON ready for database insertion

## Usage

### Command: `suggest`

Analyze documents in a week folder and suggest slot configurations.

```bash
python tools/diagnostics/slot_configuration_helper.py suggest --week "F:\path\to\week\folder"
```

**Output:**
- Total slots suggested
- Teachers found
- Detailed slot configuration with:
  - Slot number
  - Subject
  - Teacher name
  - File pattern
  - Grade and homeroom
  - Document filename
  - Slot type (single-slot vs multi-slot)

**Example:**
```
Total slots suggested: 6
Teachers found: 3
  - Catarina Morais
  - Mariela Grande
  - Taina Santiago

Slot 1: ELA/SS
  Teacher: Catarina Morais
  File Pattern: Morais
  Grade: 2, Homeroom: 310
  Document: Morais 12_15 - 12_19.docx
  Type: Multi-slot (document slot 1)
```

---

### Command: `validate`

Validate existing slot configuration against document structures.

```bash
python tools/diagnostics/slot_configuration_helper.py validate --user-id <user_id> --week "F:\path\to\week\folder"
```

**Output:**
- Summary statistics (matches, mismatches, not found)
- Detailed breakdown by category:
  - **Matches:** Perfect slot number matches
  - **Single-slot mappings:** Expected behavior for single-slot documents
  - **Mismatches:** Slot number differences (informational)
  - **Not found:** Slots without matching documents

**Example:**
```
Total slots: 5
Perfect matches: 1
Single-slot mappings (expected): 2
Multi-slot mismatches: 2
Not found: 0

[MISMATCHES] (Informational)
  Slot 4: Science (Catarina Morais)
    Requested: Slot 4
    Document: Slot 3 in Morais 12_15 - 12_19.docx
    Suggestion: Update slot 4 to slot 3
```

---

### Command: `generate`

Generate configuration JSON file ready for database insertion.

```bash
python tools/diagnostics/slot_configuration_helper.py generate --week "F:\path\to\week\folder" --output config.json
```

**Output:**
- JSON file with slot configurations
- Each slot includes:
  - `slot_number`
  - `subject`
  - `grade`
  - `homeroom`
  - `primary_teacher_name`
  - `primary_teacher_file_pattern`
  - `plan_group_label`

**Example JSON:**
```json
[
  {
    "slot_number": 1,
    "subject": "ELA/SS",
    "grade": "2",
    "homeroom": "310",
    "primary_teacher_name": "Catarina Morais",
    "primary_teacher_file_pattern": "Morais",
    "plan_group_label": "Catarina Morais 2"
  }
]
```

## How It Works

### 1. Document Analysis

The tool analyzes all DOCX files in the specified week folder:
- Extracts slot structures from each document
- Identifies teachers, subjects, grades, and homerooms
- Determines if documents are single-slot or multi-slot

### 2. File Pattern Extraction

Automatically extracts file patterns from filenames:
- Tries last name first (most common)
- Falls back to first name
- Uses known patterns (Savoca, Davies, Lang, etc.)
- Extracts from filename if teacher name matches

### 3. Configuration Suggestion

Generates suggestions based on:
- Document structure (respects slot numbers in multi-slot documents)
- Teacher grouping (one slot per teacher/subject combination)
- Single-slot handling (one slot per single-slot document)

### 4. Validation Logic

Compares existing configuration with documents:
- Matches slots to documents using file patterns
- Finds subjects in documents using subject-based detection
- Identifies mismatches and provides suggestions
- Distinguishes expected (single-slot) vs unexpected (multi-slot) mismatches

## Use Cases

### 1. New User Setup

**Scenario:** New user needs to configure slots

**Steps:**
1. Run `suggest` command on a representative week folder
2. Review suggested configuration
3. Use `generate` to create JSON file
4. Import configuration into database

### 2. Configuration Validation

**Scenario:** Verify existing configuration is correct

**Steps:**
1. Run `validate` command
2. Review results
3. Address any issues found
4. Re-validate to confirm fixes

### 3. Configuration Updates

**Scenario:** Documents changed, need to update configuration

**Steps:**
1. Run `suggest` on new week folder
2. Compare with existing configuration
3. Update slots as needed
4. Validate updated configuration

## Integration Points

### Future UI Integration

The tool can be integrated into the UI to provide:
- **Interactive Configuration Wizard:**
  - Analyze documents automatically
  - Show suggestions side-by-side with current config
  - One-click apply suggestions
  - Preview before saving

- **Real-time Validation:**
  - Validate as user configures slots
  - Show warnings/errors immediately
  - Provide fix suggestions

- **Configuration Assistant:**
  - Auto-detect document structure
  - Suggest file patterns
  - Validate before saving

## Examples

### Example 1: Suggest Configuration for Wilson

```bash
python tools/diagnostics/slot_configuration_helper.py suggest \
  --week "F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W51"
```

**Result:** Suggests 12 slots (4 per teacher: Savoca, Lang, Davies)

### Example 2: Validate Daniela's Configuration

```bash
python tools/diagnostics/slot_configuration_helper.py validate \
  --user-id "29fa9ed7-3174-4999-86fd-40a542c28cff" \
  --week "F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W51"
```

**Result:** Shows 1 match, 2 single-slot mappings, 2 mismatches (informational)

### Example 3: Generate Configuration JSON

```bash
python tools/diagnostics/slot_configuration_helper.py generate \
  --week "F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W51" \
  --output wilson_config.json
```

**Result:** Creates JSON file ready for database import

## Technical Details

### Class: `SlotConfigurationHelper`

**Methods:**
- `analyze_week_folder(week_folder_path)`: Analyze documents
- `suggest_slot_configuration(week_folder_path, user_id)`: Generate suggestions
- `validate_configuration(user_id, week_folder_path)`: Validate existing config
- `generate_configuration_json(week_folder_path, user_id)`: Generate JSON
- `_extract_file_pattern(filename, teacher_name)`: Extract file pattern

### Dependencies

- `backend.supabase_database.SupabaseDatabase`: Database access
- `tools.diagnostics.analyze_slot_structures.analyze_week_folder`: Document analysis

### Output Formats

**Suggestions:**
- Human-readable console output
- Structured dictionary with all details

**Validation:**
- Human-readable console output
- Structured dictionary with results

**Generate:**
- JSON file format
- Ready for database insertion

## Best Practices

1. **Use Representative Week:**
   - Choose a week with all teachers' files
   - Ensures complete configuration

2. **Review Suggestions:**
   - Always review before applying
   - Verify file patterns are correct
   - Check grade/homeroom information

3. **Validate After Changes:**
   - Run validation after configuration changes
   - Address any issues found
   - Re-validate to confirm

4. **Test with Multiple Weeks:**
   - Validate across multiple weeks
   - Ensure consistency
   - Handle week-to-week variations

## Limitations

1. **File Pattern Detection:**
   - Relies on filename patterns
   - May need manual adjustment for unusual filenames

2. **Subject Matching:**
   - Uses case-insensitive matching
   - Handles combined subjects (ELA/SS)
   - May need adjustment for subject name variations

3. **Single Week Analysis:**
   - Analyzes one week at a time
   - May need to run for multiple weeks
   - Consider week-to-week variations

## Future Enhancements

1. **Multi-Week Analysis:**
   - Analyze multiple weeks at once
   - Detect patterns across weeks
   - Handle week-to-week variations

2. **Auto-Configuration:**
   - Automatically create slots in database
   - Preview before applying
   - Rollback capability

3. **UI Integration:**
   - Interactive wizard
   - Real-time validation
   - Visual comparison

4. **Advanced Matching:**
   - Fuzzy matching for file patterns
   - Subject alias support
   - Grade/homeroom validation

## Troubleshooting

### Issue: No documents found

**Solution:**
- Verify week folder path is correct
- Check that DOCX files exist in folder
- Ensure files are not output files (excluded automatically)

### Issue: File pattern not detected

**Solution:**
- Check filename format
- Verify teacher name in filename
- Manually set file pattern if needed

### Issue: Subject not found

**Solution:**
- Verify subject name matches exactly
- Check for typos or variations
- Review document metadata

## Files

- **Tool:** `tools/diagnostics/slot_configuration_helper.py`
- **Documentation:** `docs/SLOT_CONFIGURATION_HELPER.md`

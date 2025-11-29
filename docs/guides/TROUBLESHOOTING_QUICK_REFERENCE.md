# Troubleshooting Quick Reference
## Bilingual Lesson Plan Builder

**Version:** 1.0.0 | **Date:** 2025-10-04

---

## Quick Diagnostics

### Is the system running?
```bash
curl http://localhost:8000/api/health
```
**Expected:** `{"status": "healthy"}`

### Can I access the docs?
```
http://localhost:8000/api/docs
```
**Expected:** Interactive API documentation page

---

## Common Errors & Solutions

### 1. Connection Refused

**Error:**
```
Failed to connect to localhost:8000
Connection refused
```

**Cause:** Server is not running

**Solution:**
```bash
# Start the server
uvicorn backend.api:app --host 127.0.0.1 --port 8000

# Or check if it's running on a different port
netstat -an | findstr "8000"
```

**Prevention:** Always check system health before starting work

---

### 2. Missing Required Field

**Error:**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "metadata.teacher_name",
      "message": "Field required"
    }
  ]
}
```

**Cause:** Required field is missing from JSON

**Solution:**
Add the missing field:
```json
"metadata": {
  "week_of": "10/6-10/10",
  "grade": "7",
  "subject": "Math",
  "teacher_name": "Ms. Smith"  // Add this
}
```

**Required Fields:**
- `metadata.week_of`
- `metadata.grade`
- `metadata.subject`
- `metadata.teacher_name`
- `days.monday` through `days.friday`

---

### 3. Invalid Date Format

**Error:**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "metadata.week_of",
      "message": "Invalid date format"
    }
  ]
}
```

**Cause:** Date is not in MM/DD-MM/DD format

**Wrong:**
```json
"week_of": "October 6-10"
"week_of": "10/6/2024-10/10/2024"
"week_of": "2024-10-06"
```

**Correct:**
```json
"week_of": "10/6-10/10"
```

**Format:** `MM/DD-MM/DD` (month/day-month/day)

---

### 4. Missing Days

**Error:**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "days.friday",
      "message": "Field required"
    }
  ]
}
```

**Cause:** Not all five weekdays are included

**Solution:**
Include all five days (even with placeholder content):
```json
"days": {
  "monday": { "unit_lesson": "Unit One" },
  "tuesday": { "unit_lesson": "TBD" },
  "wednesday": { "unit_lesson": "TBD" },
  "thursday": { "unit_lesson": "TBD" },
  "friday": { "unit_lesson": "TBD" }
}
```

**Required Days:** monday, tuesday, wednesday, thursday, friday

---

### 5. JSON Syntax Error

**Error:**
```
Expecting ',' delimiter: line 45 column 3
Expecting property name enclosed in double quotes
Unexpected token
```

**Cause:** Invalid JSON syntax

**Common Issues:**
- Missing comma between properties
- Missing closing bracket/brace
- Unbalanced quotes
- Trailing comma

**Solution:**
1. Use a JSON validator: https://jsonlint.com
2. Check for common syntax issues:
   ```json
   // Wrong - missing comma
   {
     "field1": "value1"
     "field2": "value2"
   }
   
   // Correct
   {
     "field1": "value1",
     "field2": "value2"
   }
   ```

**Tools:**
- Online: jsonlint.com
- VS Code: Built-in JSON validation
- Command line: `python -m json.tool your_file.json`

---

### 6. Template Not Found

**Error:**
```json
{
  "success": false,
  "error": "Template file not found"
}
```

**Cause:** District template file is missing or in wrong location

**Solution:**
1. Check file exists:
   ```bash
   dir "input\Lesson Plan Template SY'25-26.docx"
   ```

2. Verify path is correct

3. Check file permissions

4. Contact support if file is missing

**Expected Location:** `input/Lesson Plan Template SY'25-26.docx`

---

### 7. Rendering Failed

**Error:**
```json
{
  "success": false,
  "error": "Failed to render document"
}
```

**Cause:** Error during DOCX generation

**Solutions:**
1. Validate JSON first:
   ```bash
   curl -X POST http://localhost:8000/api/validate \
     -H "Content-Type: application/json" \
     -d @your_file.json
   ```

2. Check disk space

3. Verify output directory exists and is writable

4. Review error logs for details

5. Try with a minimal example first

---

### 8. Validation Passes But Output Looks Wrong

**Issue:** DOCX generates but formatting is incorrect

**Possible Causes:**
- Special characters in content
- Incorrect markdown syntax
- Template version mismatch
- Content too long for template cells

**Solutions:**
1. Check for special characters (curly quotes, em dashes)
2. Verify markdown syntax:
   - `**bold**` not `<b>bold</b>`
   - `*italic*` not `<i>italic</i>`
3. Ensure template is latest version
4. Keep content concise for table cells

---

### 9. Slow Performance

**Issue:** Generation takes longer than expected

**Expected Performance:**
- Validation: ~3ms
- Rendering: ~34ms
- Total: <100ms

**If Slower:**
1. Check system resources (CPU, memory)
2. Close other applications
3. Restart the server
4. Check for large content (very long text)
5. Contact support if persistent

---

### 10. File Won't Open in Word

**Issue:** Generated DOCX won't open or shows errors

**Solutions:**
1. Verify file downloaded completely
2. Check file size (should be >100KB)
3. Try opening with different Word version
4. Regenerate the document
5. Check for antivirus interference

---

## Validation Checklist

Before generating a DOCX, verify:

- [ ] All required metadata fields present
- [ ] Date in MM/DD-MM/DD format
- [ ] All five weekdays included
- [ ] Valid JSON syntax (no syntax errors)
- [ ] Content uses markdown formatting
- [ ] No special characters that might break formatting
- [ ] Validation endpoint returns `"valid": true`

---

## Quick Commands

### Check System Health
```bash
curl http://localhost:8000/api/health
```

### Validate JSON
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @your_file.json
```

### Generate DOCX
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d @your_file.json \
  -o output.docx
```

### Start Server
```bash
uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### Validate JSON Syntax
```bash
python -m json.tool your_file.json
```

---

## Error Message Decoder

| Error Message | Meaning | Quick Fix |
|--------------|---------|-----------|
| "Field required" | Missing required field | Add the field |
| "Invalid date format" | Date not MM/DD-MM/DD | Fix date format |
| "Expecting ',' delimiter" | JSON syntax error | Add missing comma |
| "Connection refused" | Server not running | Start server |
| "Template not found" | Missing template file | Check file location |
| "Validation failed" | JSON doesn't match schema | Check error details |
| "Unexpected token" | JSON syntax error | Use JSON validator |

---

## When to Contact Support

Contact support if:
- Server won't start
- Template file is missing
- Persistent validation errors you can't resolve
- Performance is consistently slow
- Generated DOCX is corrupted
- You need help with complex lesson plans

**Support Information:**
- Email: [support email]
- Phone: [support phone]
- Office Hours: [schedule]

**Include When Reporting:**
- What you were trying to do
- Error message (exact text)
- Your JSON file (if possible)
- Steps to reproduce
- Screenshots (if helpful)

---

## Best Practices to Avoid Issues

### 1. Always Validate First
Never skip validation. It catches 99% of issues before rendering.

### 2. Use Example Files as Templates
Start with working examples from `tests/fixtures/`

### 3. Make Incremental Changes
Add content gradually and validate frequently

### 4. Keep Backups
Save working versions of your JSON files

### 5. Use Consistent Formatting
Follow the same structure for all lesson plans

### 6. Test with Minimal Content First
Verify basic structure before adding complex content

### 7. Check System Health Regularly
Start each session with a health check

---

## Quick Reference: Required Structure

### Minimal Valid JSON
```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "7",
    "subject": "Math",
    "homeroom": "302",
    "teacher_name": "Ms. Smith"
  },
  "days": {
    "monday": { "unit_lesson": "Unit One" },
    "tuesday": { "unit_lesson": "Unit Two" },
    "wednesday": { "unit_lesson": "Unit Three" },
    "thursday": { "unit_lesson": "Unit Four" },
    "friday": { "unit_lesson": "Unit Five" }
  }
}
```

### Complete Day Structure
```json
"monday": {
  "unit_lesson": "Unit One Lesson One",
  "objective": {
    "content_objective": "Students will...",
    "student_goal": "I will...",
    "wida_objective": "Students will use language to..."
  },
  "anticipatory_set": {
    "original_content": "..."
  },
  "tailored_instruction": {
    "original_content": "...",
    "materials": ["Material 1", "Material 2"]
  },
  "misconceptions": {
    "original_content": "..."
  },
  "assessment": {
    "primary_assessment": "..."
  },
  "homework": {
    "original_content": "..."
  }
}
```

---

## Resources

**Documentation:**
- Quick Start Guide: `QUICK_START_GUIDE.md`
- User Training Guide: `USER_TRAINING_GUIDE.md`
- API Docs: http://localhost:8000/api/docs

**Example Files:**
- `tests/fixtures/uat_example_math.json`
- `tests/fixtures/uat_example_ela.json`
- `tests/fixtures/uat_example_science.json`
- `tests/fixtures/uat_example_bilingual.json`

**Validation Tools:**
- Online: https://jsonlint.com
- Command line: `python -m json.tool`
- VS Code: Built-in JSON validation

---

**Keep this reference handy during your work!**  
**Most issues can be resolved in under 5 minutes.** 🛠️

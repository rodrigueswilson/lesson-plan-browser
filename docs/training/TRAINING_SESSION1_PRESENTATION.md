# Training Session 1: Bilingual Lesson Plan Builder

**Date:** 2025-10-04  
**Duration:** 4 hours  
**Audience:** Teachers and Administrators  
**Presenter:** [Your Name]

---

## Session Agenda

### Morning Session (2 hours)
- 9:00 - 9:15: System Overview (15 min)
- 9:15 - 9:45: Quick Start (30 min)
- 9:45 - 10:30: Live Demonstration (45 min)
- 10:30 - 10:45: Break (15 min)

### Afternoon Session (2 hours)
- 1:00 - 2:00: Hands-On Practice (60 min)
- 2:00 - 2:30: Troubleshooting (30 min)
- 2:30 - 3:00: Q&A Session (30 min)

---

## Part 1: System Overview (15 min)

### What is the Bilingual Lesson Plan Builder?

**Purpose:**
- Generates professional DOCX lesson plans from structured data
- Ensures WIDA compliance and bilingual support
- Maintains consistent formatting across all plans

**Key Benefits:**
- **87x faster** than manual creation
- **Consistent quality** - same format every time
- **Real-time validation** - catch errors before rendering
- **Professional output** - district-approved formatting

### How It Works

```
JSON Input → Validation → Rendering → DOCX Output
   (You)      (System)     (System)    (Download)
```

**The Process:**
1. You create a JSON file with your lesson plan data
2. System validates the structure and content
3. System renders the DOCX using the district template
4. You download the formatted document

### Performance Improvements

**Before (Manual):**
- Time: ~45 minutes per week
- Errors: Frequent formatting issues
- Consistency: Varies by teacher

**After (Automated):**
- Time: ~30 seconds per week
- Errors: Caught before rendering
- Consistency: 100% uniform

**Real Numbers:**
- Validation: 3ms average
- Rendering: 34ms average
- Total: Under 1 second!

---

## Part 2: Quick Start (30 min)

### Step 1: Access the System

**API Interface (Current):**
- URL: http://localhost:8000
- Documentation: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/api/health

**Desktop App (Future):**
- Double-click icon
- Automatic startup
- User-friendly interface

### Step 2: Check System Health

**Using Browser:**
1. Open http://localhost:8000/api/health
2. Should see: `{"status": "healthy"}`

**Using Command Line:**
```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-04T09:00:00.000000"
}
```

### Step 3: Understand the JSON Format

**Basic Structure:**
```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "7",
    "subject": "Social Studies",
    "homeroom": "302",
    "teacher_name": "Ms. Smith"
  },
  "days": {
    "monday": { ... },
    "tuesday": { ... },
    "wednesday": { ... },
    "thursday": { ... },
    "friday": { ... }
  }
}
```

**Required Fields:**
- Metadata: week_of, grade, subject, teacher_name
- Days: All five weekdays (Monday-Friday)
- Each day: unit_lesson, objective, anticipatory_set, etc.

### Step 4: Validate Your First JSON

**Using the Interactive Docs:**
1. Go to http://localhost:8000/api/docs
2. Click on `/api/validate`
3. Click "Try it out"
4. Paste example JSON
5. Click "Execute"
6. Review results

**Using Command Line:**
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/uat_example_math.json
```

### Step 5: Generate Your First DOCX

**Using the Interactive Docs:**
1. Click on `/api/render`
2. Click "Try it out"
3. Paste validated JSON
4. Click "Execute"
5. Download the file

**Using Command Line:**
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/uat_example_math.json \
  -o my_first_lesson_plan.docx
```

---

## Part 3: Live Demonstration (45 min)

### Demo 1: Simple Math Lesson Plan (15 min)

**Scenario:**
- Grade 6 Math
- Week of 10/6-10/10
- Topic: Fractions

**Steps:**
1. Open `tests/fixtures/uat_example_math.json`
2. Review the structure
3. Validate the JSON
4. Generate the DOCX
5. Open in Microsoft Word
6. Review the output

**Key Points to Highlight:**
- Clean, professional formatting
- District template preserved
- All content properly placed
- Bilingual support included

### Demo 2: Bilingual Science Lesson (15 min)

**Scenario:**
- Grade 7 Science
- High ELL population
- Co-teaching model

**Steps:**
1. Open `tests/fixtures/uat_example_bilingual.json`
2. Show bilingual overlays
3. Show co-teaching model
4. Show ELL support strategies
5. Generate and review

**Key Points to Highlight:**
- Bilingual bridges
- L1 support
- Cognate awareness
- Family connections

### Demo 3: Error Handling (15 min)

**Scenario:**
- Intentionally broken JSON
- Missing required fields
- Invalid data types

**Steps:**
1. Open `tests/fixtures/invalid_missing_required.json`
2. Attempt validation
3. Review error messages
4. Fix the errors
5. Validate successfully

**Key Points to Highlight:**
- Clear error messages
- Specific field identification
- Easy to fix
- Prevents bad output

---

## Part 4: Hands-On Practice (60 min)

### Exercise 1: Validate an Example (10 min)

**Your Task:**
1. Open http://localhost:8000/api/docs
2. Navigate to `/api/validate`
3. Copy the JSON from `tests/fixtures/uat_example_ela.json`
4. Validate it
5. Verify it passes

**Success Criteria:**
- Validation returns `"valid": true`
- No errors reported
- You understand the response

### Exercise 2: Generate Your First DOCX (15 min)

**Your Task:**
1. Use the same JSON from Exercise 1
2. Navigate to `/api/render`
3. Generate the DOCX
4. Download the file
5. Open in Microsoft Word

**Success Criteria:**
- DOCX generates successfully
- File opens in Word
- Formatting looks correct
- All content is present

### Exercise 3: Create a Simple Lesson Plan (20 min)

**Your Task:**
Create a lesson plan for:
- Your subject
- Your grade level
- This week's dates
- One day only (Monday)

**Template to Use:**
```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "YOUR_GRADE",
    "subject": "YOUR_SUBJECT",
    "homeroom": "YOUR_ROOM",
    "teacher_name": "YOUR_NAME"
  },
  "days": {
    "monday": {
      "unit_lesson": "Unit One Lesson One",
      "objective": {
        "content_objective": "Students will...",
        "student_goal": "I will...",
        "wida_objective": "Students will use language to..."
      },
      "anticipatory_set": {
        "original_content": "Your anticipatory set here"
      },
      "tailored_instruction": {
        "original_content": "Your instruction here",
        "materials": ["Material 1", "Material 2"]
      },
      "misconceptions": {
        "original_content": "Common misconceptions"
      },
      "assessment": {
        "primary_assessment": "Exit ticket"
      },
      "homework": {
        "original_content": "Homework assignment"
      }
    },
    "tuesday": { "unit_lesson": "TBD" },
    "wednesday": { "unit_lesson": "TBD" },
    "thursday": { "unit_lesson": "TBD" },
    "friday": { "unit_lesson": "TBD" }
  }
}
```

**Success Criteria:**
- JSON validates successfully
- DOCX generates
- Content is accurate
- You feel confident

### Exercise 4: Add Bilingual Support (15 min)

**Your Task:**
Enhance your Monday lesson with:
- Bilingual bridge in anticipatory set
- ELL support strategies
- Co-teaching model (if applicable)

**Example Additions:**
```json
"anticipatory_set": {
  "original_content": "Review prior knowledge",
  "bilingual_bridge": "Preview key cognates: fraction/fração, numerator/numerador"
},
"tailored_instruction": {
  "original_content": "Teach fractions",
  "ell_support": [
    {
      "strategy_name": "Visual Aids",
      "implementation": "Use fraction circles and bars"
    },
    {
      "strategy_name": "Sentence Frames",
      "implementation": "The numerator is ___, the denominator is ___"
    }
  ]
}
```

**Success Criteria:**
- Bilingual elements added
- Validates successfully
- Output includes all enhancements
- You understand the structure

---

## Part 5: Troubleshooting (30 min)

### Common Error 1: Missing Required Fields

**Error Message:**
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

**Solution:**
- Check the error message for the specific field
- Add the missing field to your JSON
- Validate again

**Example Fix:**
```json
"metadata": {
  "week_of": "10/6-10/10",
  "grade": "7",
  "subject": "Math",
  "teacher_name": "Ms. Smith"  // Added this line
}
```

### Common Error 2: Invalid Date Format

**Error Message:**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "metadata.week_of",
      "message": "Invalid date format. Use MM/DD-MM/DD"
    }
  ]
}
```

**Solution:**
- Use the correct format: MM/DD-MM/DD
- Example: "10/6-10/10" not "Oct 6-10"

### Common Error 3: Missing Days

**Error Message:**
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

**Solution:**
- All five weekdays are required
- Add placeholder content if needed
- Example: `"friday": { "unit_lesson": "TBD" }`

### Common Error 4: JSON Syntax Errors

**Error Message:**
```
Expecting ',' delimiter: line 45 column 3
```

**Solution:**
- Use a JSON validator (jsonlint.com)
- Check for missing commas
- Check for missing brackets
- Verify quotes are balanced

### Common Error 5: Template Not Found

**Error Message:**
```json
{
  "success": false,
  "error": "Template file not found"
}
```

**Solution:**
- Verify template exists: `input/Lesson Plan Template SY'25-26.docx`
- Check file permissions
- Contact support if persistent

---

## Part 6: Q&A Session (30 min)

### Frequently Asked Questions

**Q: How long does it take to create a lesson plan?**
A: About 5-10 minutes for a full week, once you're familiar with the format.

**Q: Can I edit the DOCX after generation?**
A: Yes! Open it in Word and edit as needed.

**Q: What if I make a mistake?**
A: Just fix your JSON and regenerate. It's quick!

**Q: Do I need to include all five days?**
A: Yes, but you can use placeholder content for days you haven't planned yet.

**Q: Can I use this for multiple classes?**
A: Yes! Create separate JSON files for each class.

**Q: What about special formatting?**
A: Use markdown: `**bold**` and `*italic*` in your content.

**Q: How do I add bilingual support?**
A: Use the bilingual_bridge, ell_support, and co_teaching_model fields.

**Q: What if validation fails?**
A: Read the error message - it tells you exactly what's wrong and where.

**Q: Can I save my lesson plans?**
A: Yes! Save your JSON files for future use or modification.

**Q: Who do I contact for help?**
A: [Your support contact information]

### Open Discussion

**Topics to Cover:**
- Specific use cases
- Integration with existing workflow
- Feature requests
- Concerns or challenges
- Success stories

---

## Wrap-Up and Next Steps

### What We Covered Today

1. System overview and benefits
2. How to access and use the API
3. JSON structure and validation
4. Generating DOCX files
5. Troubleshooting common issues

### Your Action Items

- [ ] Practice with the example files
- [ ] Create a lesson plan for your class
- [ ] Review the User Training Guide
- [ ] Bookmark the API documentation
- [ ] Share feedback with the team

### Resources

**Documentation:**
- Quick Start Guide: `QUICK_START_GUIDE.md`
- User Training Guide: `USER_TRAINING_GUIDE.md`
- API Docs: http://localhost:8000/api/docs

**Examples:**
- `tests/fixtures/uat_example_math.json`
- `tests/fixtures/uat_example_ela.json`
- `tests/fixtures/uat_example_science.json`
- `tests/fixtures/uat_example_bilingual.json`

**Support:**
- Email: [support email]
- Phone: [support phone]
- Office Hours: [schedule]

### Training Session 2 Preview

**Coming Soon:**
- Advanced features
- Batch processing
- Custom templates
- Integration strategies
- Power user tips

---

## Feedback Form

**Please provide feedback on:**
1. Clarity of presentation (1-10)
2. Usefulness of hands-on exercises (1-10)
3. Confidence level after training (1-10)
4. What worked well?
5. What could be improved?
6. Additional topics needed?

---

**Thank you for attending Training Session 1!**  
**Questions? Contact [support]** 🎉

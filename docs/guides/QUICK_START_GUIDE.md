# Quick Start Guide - Bilingual Lesson Plan Builder

**Version:** 1.0.0  
**For:** Teachers and Administrators  
**Last Updated:** 2025-10-04

---

## What is This?

The Bilingual Lesson Plan Builder is a tool that generates professional lesson plan documents (DOCX) from structured JSON data. It's **87x faster** than manual creation and ensures consistent formatting.

---

## How to Use It

### Step 1: Access the API

The system runs on your local machine:
- **URL:** http://localhost:8000
- **Documentation:** http://localhost:8000/api/docs

### Step 2: Prepare Your Lesson Plan Data

Create a JSON file with your lesson plan information. Here's a minimal example:

```json
{
  "metadata": {
    "teacher_name": "Your Name",
    "subject": "Social Studies",
    "grade_level": "6",
    "week_of": "2024-09-15"
  },
  "daily_plans": {
    "monday": {
      "objective": "Students will understand Roman civilization",
      "anticipatory_set": {
        "original_content": "Review prior knowledge"
      },
      "instructional_input": {
        "original_content": "Lecture on Roman history"
      },
      "guided_practice": {
        "original_content": "Group discussion"
      },
      "independent_practice": {
        "original_content": "Individual worksheet"
      },
      "assessment": {
        "original_content": "Exit ticket"
      },
      "homework": {
        "original_content": "Read chapter 5"
      }
    }
  }
}
```

### Step 3: Validate Your JSON

Before generating the document, validate your JSON:

**Using the API:**
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @your_lesson_plan.json
```

**Expected Response:**
```json
{
  "valid": true,
  "errors": null,
  "warnings": null
}
```

### Step 4: Generate Your DOCX

Once validated, generate the document:

**Using the API:**
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d @your_lesson_plan.json \
  -o lesson_plan.docx
```

**Expected Response:**
```json
{
  "success": true,
  "output_path": "output/lesson_plan.docx",
  "file_size": 282847,
  "render_time_ms": 34.26
}
```

### Step 5: Download Your Document

The generated DOCX file will be in the `output` folder. You can also download it via the API:

```bash
curl http://localhost:8000/api/render/lesson_plan.docx -o my_lesson_plan.docx
```

---

## Using the Interactive Documentation

The easiest way to use the system is through the interactive documentation:

1. Open http://localhost:8000/api/docs in your browser
2. Click on any endpoint (e.g., `/api/validate`)
3. Click "Try it out"
4. Paste your JSON data
5. Click "Execute"
6. View the response

---

## Common Tasks

### Task 1: Check System Health

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-04T23:10:00.000000"
}
```

### Task 2: Validate a Lesson Plan

```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"json_data": {...your lesson plan...}}'
```

### Task 3: Generate a DOCX

```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d '{"json_data": {...your lesson plan...}, "output_filename": "my_plan.docx"}'
```

---

## Tips & Best Practices

### 1. Always Validate First
- Validate your JSON before rendering
- Fix any errors before proceeding
- Check warnings for potential issues

### 2. Use Descriptive Filenames
- Include date: `lesson_plan_20240915.docx`
- Include subject: `social_studies_week1.docx`
- Include grade: `grade6_history.docx`

### 3. Keep JSON Files Organized
- Store in a dedicated folder
- Use version control if possible
- Back up regularly

### 4. Check Output Quality
- Open generated DOCX in Word
- Verify formatting
- Check all content is present
- Review bilingual overlays

---

## Troubleshooting

### Problem: "Connection refused"

**Solution:** Make sure the server is running:
```bash
uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### Problem: "Validation failed"

**Solution:** Check the error messages:
- Missing required fields
- Invalid data types
- Incorrect format

Use the validation endpoint to see specific errors.

### Problem: "Template not found"

**Solution:** Verify the template file exists:
```bash
ls "input/Lesson Plan Template SY'25-26.docx"
```

### Problem: "Slow performance"

**Solution:**
- Close other applications
- Check system resources
- Contact support if persistent

---

## Performance Expectations

**Typical Performance:**
- Validation: ~3ms
- Rendering: ~34ms
- Total workflow: ~50ms

**What This Means:**
- You can generate lesson plans in under 1 second
- 87x faster than manual creation
- Process multiple plans quickly

---

## Getting Help

### Documentation
- **User Training Guide:** `USER_TRAINING_GUIDE.md`
- **API Documentation:** http://localhost:8000/api/docs
- **Production Guide:** `README_PRODUCTION.md`

### Support Channels
- **Email:** [support email]
- **Phone:** [support phone]
- **Office Hours:** [schedule]

### Common Questions
- See `USER_TRAINING_GUIDE.md` FAQ section
- Check troubleshooting section above
- Contact support team

---

## Next Steps

1. **Try the Examples**
   - Use `tests/fixtures/valid_lesson_minimal.json`
   - Generate your first DOCX
   - Verify the output

2. **Create Your Own**
   - Start with the minimal example
   - Add your lesson plan content
   - Validate and render

3. **Explore Advanced Features**
   - Bilingual overlays
   - Co-teaching models
   - ELL support strategies
   - WIDA objectives

4. **Get Training**
   - Attend training sessions
   - Practice with examples
   - Ask questions

---

## Success Checklist

- [ ] Accessed http://localhost:8000/api/docs
- [ ] Validated a sample JSON file
- [ ] Generated your first DOCX
- [ ] Opened the DOCX in Word
- [ ] Created your own lesson plan
- [ ] Understand how to get help

---

**Welcome to the Bilingual Lesson Plan Builder!**  
**We're here to make your lesson planning faster and easier.** 🚀

---

*For detailed information, see the complete User Training Guide.*

# Hands-On Training Workbook
## Bilingual Lesson Plan Builder

**Version:** 1.0.0  
**Date:** 2025-10-04  
**Your Name:** ___________________  
**Subject:** ___________________  
**Grade:** ___________________

---

## Welcome!

This workbook will guide you through practical exercises to master the Bilingual Lesson Plan Builder. Complete each exercise at your own pace, and don't hesitate to ask questions!

---

## Exercise 1: System Health Check (5 min)

### Objective
Verify that the system is running and accessible.

### Steps

**1. Open your web browser**

**2. Navigate to the health endpoint:**
```
http://localhost:8000/api/health
```

**3. Record what you see:**
```
Status: ___________________
Version: ___________________
Timestamp: ___________________
```

**4. Alternative: Use command line (optional)**
```bash
curl http://localhost:8000/api/health
```

### Success Criteria
- [ ] Page loads successfully
- [ ] Status shows "healthy"
- [ ] Version number is displayed
- [ ] You understand how to check system health

### Troubleshooting
If you see an error:
- Check that the server is running
- Verify the URL is correct
- Ask for assistance

---

## Exercise 2: Explore the API Documentation (10 min)

### Objective
Familiarize yourself with the interactive API documentation.

### Steps

**1. Open the API documentation:**
```
http://localhost:8000/api/docs
```

**2. Explore the available endpoints:**
- [ ] `/api/health` - System health check
- [ ] `/api/validate` - Validate JSON structure
- [ ] `/api/render` - Generate DOCX file
- [ ] `/api/schema` - View JSON schema

**3. Click on `/api/health`**
- [ ] Click "Try it out"
- [ ] Click "Execute"
- [ ] Review the response

**4. Record your observations:**
```
What information does the response provide?
_________________________________________________
_________________________________________________
```

### Success Criteria
- [ ] Documentation page loads
- [ ] You can see all endpoints
- [ ] You successfully executed a test request
- [ ] You understand the interface

---

## Exercise 3: Validate Your First JSON (15 min)

### Objective
Learn how to validate a lesson plan JSON file.

### Steps

**1. Open the example file:**
```
tests/fixtures/uat_example_math.json
```

**2. Copy the entire JSON content**

**3. Go to the API documentation:**
```
http://localhost:8000/api/docs
```

**4. Navigate to `/api/validate`**
- [ ] Click "Try it out"
- [ ] Paste the JSON in the request body
- [ ] Click "Execute"

**5. Review the response:**
```json
{
  "valid": true/false,
  "errors": [...],
  "warnings": [...]
}
```

**6. Record the results:**
```
Valid: ___________________
Number of errors: ___________________
Number of warnings: ___________________
```

### Success Criteria
- [ ] Validation completes successfully
- [ ] Response shows `"valid": true`
- [ ] No errors reported
- [ ] You understand the validation process

### Challenge
Try validating `tests/fixtures/invalid_missing_required.json` and see what errors appear!

---

## Exercise 4: Generate Your First DOCX (15 min)

### Objective
Generate a complete lesson plan document from JSON.

### Steps

**1. Use the validated JSON from Exercise 3**

**2. Go to `/api/render` in the API docs**

**3. Generate the document:**
- [ ] Click "Try it out"
- [ ] Paste the JSON in the request body
- [ ] (Optional) Set output_filename to "my_first_lesson.docx"
- [ ] Click "Execute"

**4. Review the response:**
```json
{
  "success": true,
  "output_path": "...",
  "file_size": ...,
  "render_time_ms": ...
}
```

**5. Record the results:**
```
Success: ___________________
File size: ___________________
Render time: ___________________
```

**6. Download the file:**
- [ ] Click "Download file" in the response
- [ ] Save to your computer
- [ ] Open in Microsoft Word

**7. Review the output:**
- [ ] Check formatting
- [ ] Verify all content is present
- [ ] Review bilingual elements
- [ ] Check for any issues

### Success Criteria
- [ ] DOCX generates successfully
- [ ] File downloads correctly
- [ ] Opens in Microsoft Word
- [ ] Formatting looks professional
- [ ] All content is accurate

### Observations
```
What do you like about the output?
_________________________________________________
_________________________________________________

What questions do you have?
_________________________________________________
_________________________________________________
```

---

## Exercise 5: Create a Simple Lesson Plan (30 min)

### Objective
Create your own lesson plan from scratch.

### Your Lesson Plan Details

**Fill in your information:**
```
Week of: ___________________
Grade: ___________________
Subject: ___________________
Homeroom: ___________________
Teacher Name: ___________________
```

### Step 1: Create the Metadata

**Copy this template and fill in your information:**
```json
{
  "metadata": {
    "week_of": "YOUR_WEEK",
    "grade": "YOUR_GRADE",
    "subject": "YOUR_SUBJECT",
    "homeroom": "YOUR_ROOM",
    "teacher_name": "YOUR_NAME"
  },
  "days": {
  }
}
```

### Step 2: Create Monday's Lesson

**Add this to the "days" object:**
```json
"monday": {
  "unit_lesson": "Unit ___ Lesson ___",
  "objective": {
    "content_objective": "Students will ___",
    "student_goal": "I will ___",
    "wida_objective": "Students will use language to ___"
  },
  "anticipatory_set": {
    "original_content": "___"
  },
  "tailored_instruction": {
    "original_content": "___",
    "materials": ["___", "___"]
  },
  "misconceptions": {
    "original_content": "___"
  },
  "assessment": {
    "primary_assessment": "___"
  },
  "homework": {
    "original_content": "___"
  }
}
```

### Step 3: Add Placeholder Days

**Add these for Tuesday-Friday:**
```json
"tuesday": { "unit_lesson": "TBD" },
"wednesday": { "unit_lesson": "TBD" },
"thursday": { "unit_lesson": "TBD" },
"friday": { "unit_lesson": "TBD" }
```

### Step 4: Validate Your JSON

- [ ] Copy your complete JSON
- [ ] Go to `/api/validate`
- [ ] Paste and execute
- [ ] Fix any errors
- [ ] Validate again until successful

**Record any errors you encountered:**
```
Error 1: _________________________________________________
Solution: _________________________________________________

Error 2: _________________________________________________
Solution: _________________________________________________
```

### Step 5: Generate Your DOCX

- [ ] Go to `/api/render`
- [ ] Paste your validated JSON
- [ ] Generate the document
- [ ] Download and review

### Success Criteria
- [ ] JSON validates successfully
- [ ] DOCX generates without errors
- [ ] Content is accurate
- [ ] You feel confident creating lesson plans

### Reflection
```
What was easiest?
_________________________________________________

What was most challenging?
_________________________________________________

What would you do differently next time?
_________________________________________________
```

---

## Exercise 6: Add Bilingual Support (20 min)

### Objective
Enhance your Monday lesson with bilingual elements.

### Step 1: Add a Bilingual Bridge

**Enhance your anticipatory_set:**
```json
"anticipatory_set": {
  "original_content": "Your original content",
  "bilingual_bridge": "Preview key cognates: [English/Portuguese pairs]"
}
```

**Example:**
```json
"bilingual_bridge": "Preview key cognates: fraction/fração, numerator/numerador, denominator/denominador"
```

**Your bilingual bridge:**
```
_________________________________________________
_________________________________________________
```

### Step 2: Add ELL Support Strategies

**Add to your tailored_instruction:**
```json
"tailored_instruction": {
  "original_content": "Your instruction",
  "ell_support": [
    {
      "strategy_name": "Visual Aids",
      "implementation": "Use diagrams and images to support comprehension"
    },
    {
      "strategy_name": "Sentence Frames",
      "implementation": "Provide: 'The ___ is ___ because ___'"
    }
  ],
  "materials": ["Your materials"]
}
```

**Your ELL strategies:**
```
Strategy 1: _________________________________________________
Implementation: _________________________________________________

Strategy 2: _________________________________________________
Implementation: _________________________________________________
```

### Step 3: Add a Co-Teaching Model (Optional)

**If you have a co-teacher, add this:**
```json
"co_teaching_model": {
  "model_name": "Station Teaching",
  "implementation": "Three stations: teacher-led, independent practice, technology",
  "teacher_roles": "Teacher A leads station 1, Teacher B leads station 2, students rotate"
}
```

**Your co-teaching model:**
```
Model: _________________________________________________
Implementation: _________________________________________________
Roles: _________________________________________________
```

### Step 4: Validate and Generate

- [ ] Validate your enhanced JSON
- [ ] Fix any errors
- [ ] Generate the DOCX
- [ ] Compare with your previous version

### Success Criteria
- [ ] Bilingual elements added successfully
- [ ] JSON validates
- [ ] DOCX shows all enhancements
- [ ] You understand bilingual support options

### Observations
```
How does the bilingual version compare to the original?
_________________________________________________
_________________________________________________

What other bilingual elements would be helpful?
_________________________________________________
_________________________________________________
```

---

## Exercise 7: Troubleshooting Practice (15 min)

### Objective
Learn to identify and fix common errors.

### Challenge 1: Missing Required Field

**This JSON has an error. Find and fix it:**
```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "7",
    "subject": "Math"
  },
  "days": {
    "monday": { "unit_lesson": "Unit One" }
  }
}
```

**What's wrong?**
```
_________________________________________________
```

**How to fix it?**
```
_________________________________________________
```

### Challenge 2: Invalid Date Format

**This JSON has an error. Find and fix it:**
```json
{
  "metadata": {
    "week_of": "October 6-10",
    "grade": "7",
    "subject": "Math",
    "teacher_name": "Ms. Smith"
  }
}
```

**What's wrong?**
```
_________________________________________________
```

**How to fix it?**
```
_________________________________________________
```

### Challenge 3: Missing Days

**This JSON has an error. Find and fix it:**
```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "7",
    "subject": "Math",
    "teacher_name": "Ms. Smith"
  },
  "days": {
    "monday": { "unit_lesson": "Unit One" },
    "tuesday": { "unit_lesson": "Unit Two" }
  }
}
```

**What's wrong?**
```
_________________________________________________
```

**How to fix it?**
```
_________________________________________________
```

### Success Criteria
- [ ] Identified all errors
- [ ] Understood why they were errors
- [ ] Know how to fix similar issues
- [ ] Feel confident troubleshooting

---

## Exercise 8: Complete Week Plan (Optional Challenge)

### Objective
Create a complete 5-day lesson plan.

### Your Task
Expand your Monday lesson to include all five days with:
- Unique content for each day
- Progressive learning objectives
- Varied instructional strategies
- Consistent bilingual support

### Planning Template

**Monday:**
- Topic: ___________________
- Focus: ___________________

**Tuesday:**
- Topic: ___________________
- Focus: ___________________

**Wednesday:**
- Topic: ___________________
- Focus: ___________________

**Thursday:**
- Topic: ___________________
- Focus: ___________________

**Friday:**
- Topic: ___________________
- Focus: ___________________

### Steps
1. Plan your week's content
2. Create JSON for all five days
3. Validate the complete plan
4. Generate the DOCX
5. Review for consistency and flow

### Success Criteria
- [ ] All five days completed
- [ ] Content flows logically
- [ ] Objectives build on each other
- [ ] Bilingual support throughout
- [ ] Professional, polished output

---

## Post-Training Checklist

### Skills Mastered
- [ ] Check system health
- [ ] Navigate API documentation
- [ ] Validate JSON files
- [ ] Generate DOCX documents
- [ ] Create basic lesson plans
- [ ] Add bilingual support
- [ ] Troubleshoot common errors
- [ ] Create complete week plans

### Confidence Level
Rate your confidence (1-10):
```
Using the API: ___/10
Creating JSON: ___/10
Validating plans: ___/10
Generating DOCX: ___/10
Adding bilingual elements: ___/10
Troubleshooting: ___/10
Overall confidence: ___/10
```

### Next Steps
- [ ] Create lesson plans for my classes
- [ ] Experiment with advanced features
- [ ] Share with colleagues
- [ ] Provide feedback to the team
- [ ] Attend Training Session 2

---

## Feedback and Questions

### What worked well?
```
_________________________________________________
_________________________________________________
_________________________________________________
```

### What was challenging?
```
_________________________________________________
_________________________________________________
_________________________________________________
```

### What questions do you still have?
```
_________________________________________________
_________________________________________________
_________________________________________________
```

### Suggestions for improvement?
```
_________________________________________________
_________________________________________________
_________________________________________________
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

**Support:**
- Email: [support email]
- Phone: [support phone]
- Office Hours: [schedule]

---

**Congratulations on completing the training!** 🎉  
**You're ready to create professional bilingual lesson plans!**

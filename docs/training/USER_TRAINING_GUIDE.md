# User Training Guide - Bilingual Lesson Plan Builder

**Version:** 1.0.0  
**Date:** 2025-10-04  
**Audience:** Teachers and Administrators

---

## Welcome! 👋

Welcome to the Bilingual Lesson Plan Builder! This guide will help you get started with creating WIDA-enhanced bilingual lesson plans using our new JSON-based system.

### What's New?

The new system offers:
- ✅ **Faster processing** - 84x faster than before
- ✅ **Better validation** - Catches errors before rendering
- ✅ **Real-time progress** - See what's happening as it works
- ✅ **Consistent output** - Same format every time
- ✅ **Easy to use** - Simple API or future desktop app

---

## Quick Start (5 Minutes)

### Step 1: Access the System

**Option A: API (Current)**
```
http://localhost:8000/api/docs
```

**Option B: Desktop App (Future)**
- Double-click the application icon
- System starts automatically

### Step 2: Prepare Your Lesson Plan

Your lesson plan should include:
- **Metadata:** Week, grade, subject, teacher name, homeroom
- **Daily Plans:** Monday through Friday
- **For Each Day:**
  - Unit/Lesson number
  - Objectives (content, student goal, WIDA)
  - Anticipatory set
  - Tailored instruction
  - Misconceptions
  - Assessment
  - Homework

### Step 3: Create Your Lesson Plan

**Using the API:**
```bash
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d @my_lesson_plan.json
```

**Using the Desktop App (Future):**
1. Click "New Lesson Plan"
2. Fill in the form
3. Click "Generate"
4. Download your DOCX file

### Step 4: Download Your DOCX

Your formatted lesson plan will be ready in seconds!

---

## Understanding the JSON Format

### Basic Structure

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

### Daily Plan Structure

```json
"monday": {
  "unit_lesson": "Unit One Lesson Seven",
  "objective": {
    "content_objective": "Students will explain...",
    "student_goal": "I will explain...",
    "wida_objective": "Students will use language to..."
  },
  "anticipatory_set": {
    "original_content": "Students will respond...",
    "bilingual_bridge": "Preview key cognates..."
  },
  "tailored_instruction": {
    "original_content": "Engage / Introduction...",
    "co_teaching_model": { ... },
    "ell_support": [ ... ],
    "materials": [ ... ]
  },
  "misconceptions": {
    "original_content": "Students may believe...",
    "linguistic_note": { ... }
  },
  "assessment": {
    "primary_assessment": "Exit Ticket",
    "bilingual_overlay": { ... }
  },
  "homework": {
    "original_content": "Complete worksheet",
    "family_connection": "Ask family..."
  }
}
```

---

## Common Tasks

### Task 1: Create a Simple Lesson Plan

**What You Need:**
- Week dates
- Grade level
- Subject
- Basic lesson content

**Steps:**
1. Start with a template
2. Fill in metadata
3. Add daily plans
4. Generate DOCX

**Time:** 5-10 minutes per week

### Task 2: Add Bilingual Support

**What to Include:**
- Bilingual bridges
- ELL support strategies
- Co-teaching models
- Family connections

**Tips:**
- Use cognates when possible
- Include L1 support
- Provide sentence frames
- Add visual aids

### Task 3: Validate Your Lesson Plan

**Before Generating:**
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @my_lesson_plan.json
```

**What It Checks:**
- Required fields present
- Correct data types
- Valid date formats
- All days included

### Task 4: Download and Review

**After Generation:**
1. Download the DOCX file
2. Open in Microsoft Word
3. Review formatting
4. Check content accuracy
5. Make any manual edits needed

---

## Tips & Best Practices

### Writing Effective Objectives

**Content Objective:**
- Clear and measurable
- Grade-appropriate
- Aligned with standards

**Student Goal:**
- First-person ("I will...")
- Student-friendly language
- Achievable in one lesson

**WIDA Objective:**
- Includes language function
- Specifies ELD standard
- Appropriate proficiency levels

### Using Co-Teaching Models

**When to Use Each Model:**

**Station Teaching:**
- Mixed proficiency levels (4+)
- Differentiated activities
- Small group work

**Parallel Teaching:**
- Balanced proficiency distribution
- Same content, different scaffolding
- Simultaneous instruction

**Team Teaching:**
- Complex content
- Translanguaging opportunities
- Dual perspectives

**Alternative Teaching:**
- Small group needs intensive support
- Pre-teaching or re-teaching
- Targeted intervention

### Adding ELL Support

**Effective Strategies:**
- **Cognate Awareness:** Highlight Portuguese-English cognates
- **Graphic Organizers:** Visual structure for content
- **Sentence Frames:** Language scaffolds
- **Visual Aids:** Images and diagrams
- **Bilingual Glossary:** Key vocabulary in both languages

**Proficiency Levels:**
- Levels 1-2: Heavy scaffolding, L1 support
- Levels 3-4: Moderate scaffolding, transitioning
- Levels 5-6: Light scaffolding, academic language focus

---

## Troubleshooting

### Problem: Validation Errors

**Symptoms:**
- Error message when validating
- Missing required fields
- Incorrect data format

**Solutions:**
1. Check error message for specific field
2. Verify all required fields present
3. Check date format (MM/DD-MM/DD)
4. Ensure all days included (Mon-Fri)
5. Use the schema as reference

### Problem: Rendering Fails

**Symptoms:**
- Error during DOCX generation
- Incomplete output
- Missing content

**Solutions:**
1. Validate JSON first
2. Check template file exists
3. Verify file permissions
4. Check disk space
5. Review error logs

### Problem: Formatting Issues

**Symptoms:**
- DOCX looks wrong
- Missing formatting
- Incorrect layout

**Solutions:**
1. Verify template is correct version
2. Check for special characters
3. Use markdown formatting correctly
4. Review generated file in Word
5. Report persistent issues

### Problem: Performance Issues

**Symptoms:**
- Slow generation
- Timeouts
- System unresponsive

**Solutions:**
1. Check system resources
2. Close other applications
3. Simplify lesson plan if very large
4. Contact support if persistent

---

## Frequently Asked Questions

### General Questions

**Q: How long does it take to generate a lesson plan?**  
A: Typically less than 1 second! The system is 84x faster than our targets.

**Q: Can I edit the DOCX after generation?**  
A: Yes! Open it in Microsoft Word and edit as needed.

**Q: What if I make a mistake?**  
A: Just fix your JSON and regenerate. It's quick!

**Q: Can I save my lesson plans?**  
A: Yes, save your JSON files for future use or modification.

### Technical Questions

**Q: What format should dates be in?**  
A: Use MM/DD-MM/DD format, e.g., "10/6-10/10"

**Q: Do I need all five days?**  
A: Yes, Monday through Friday are required.

**Q: Can I use markdown formatting?**  
A: Yes! Use `**bold**` and `*italic*` in your content.

**Q: What if validation fails?**  
A: Check the error message - it tells you exactly what's wrong.

### Support Questions

**Q: Who do I contact for help?**  
A: [Your support contact information]

**Q: Is there training available?**  
A: Yes! Check the training schedule or request a session.

**Q: Where is the documentation?**  
A: All documentation is in the `docs/` folder or at [URL]

**Q: Can I request new features?**  
A: Absolutely! Send your ideas to [contact]

---

## Examples

### Example 1: Minimal Lesson Plan

See `tests/fixtures/valid_lesson_minimal.json` for a complete working example.

**Key Points:**
- All required fields included
- Proper JSON structure
- Valid data types
- Correct date format

### Example 2: Full-Featured Lesson Plan

Includes:
- Complete metadata
- All daily plans
- Co-teaching models
- ELL support strategies
- Bilingual overlays
- Family connections

### Example 3: Station Teaching Model

Shows:
- Multiple stations
- Rotation schedule
- Differentiated activities
- Teacher roles
- Implementation notes

---

## Getting Help

### Self-Service Resources

1. **This Guide** - Start here!
2. **API Documentation** - http://localhost:8000/api/docs
3. **Schema Reference** - `schemas/lesson_output_schema.json`
4. **Example Files** - `tests/fixtures/`
5. **Implementation Guides** - `PHASE*_IMPLEMENTATION.md`

### Support Channels

**Email:** [support email]  
**Phone:** [support phone]  
**Office Hours:** [schedule]  
**Documentation:** [URL]

### Reporting Issues

**Include:**
- What you were trying to do
- What happened instead
- Error messages
- Your JSON file (if possible)
- Screenshots (if helpful)

---

## Next Steps

### After This Training

1. **Practice** - Try creating a simple lesson plan
2. **Experiment** - Test different features
3. **Ask Questions** - Don't hesitate to reach out
4. **Share Feedback** - Help us improve!

### Advanced Topics

- Custom templates
- Batch processing
- API integration
- Advanced formatting
- Performance optimization

### Stay Updated

- Check for system updates
- Review new documentation
- Attend training sessions
- Join user community

---

## Appendix

### Keyboard Shortcuts (Future Desktop App)

- `Ctrl+N` - New lesson plan
- `Ctrl+O` - Open lesson plan
- `Ctrl+S` - Save lesson plan
- `Ctrl+G` - Generate DOCX
- `F1` - Help

### Glossary

**API:** Application Programming Interface - how programs talk to each other  
**DOCX:** Microsoft Word document format  
**ELL:** English Language Learner  
**JSON:** JavaScript Object Notation - data format  
**SSE:** Server-Sent Events - real-time updates  
**WIDA:** World-Class Instructional Design and Assessment

### Additional Resources

- WIDA Framework: [URL]
- Co-Teaching Models: [URL]
- Bilingual Strategies: [URL]
- JSON Tutorial: [URL]

---

**Training Guide Version:** 1.0.0  
**Last Updated:** 2025-10-04  
**Questions?** Contact [support]

---

*Thank you for using the Bilingual Lesson Plan Builder!* 🎉

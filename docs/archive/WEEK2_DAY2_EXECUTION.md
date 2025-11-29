# Week 2, Day 2: User Acceptance Testing - Execution

**Date:** 2025-10-05  
**Status:** IN PROGRESS  
**Duration:** 4 hours

---

## Morning Session: Guided Walkthrough

### Test User Profiles

For this UAT, we'll simulate testing with three user personas:

**User 1: Experienced Teacher (Ms. Davies)**
- 10+ years teaching experience
- Currently uses manual Word documents
- Teaches Social Studies, Grade 6
- Familiar with current lesson planning process
- Tech-comfortable but not expert

**User 2: New Teacher (Mr. Lang)**
- 2 years teaching experience
- Digital native, comfortable with technology
- Teaches multiple subjects
- Looking for efficiency improvements
- Open to new tools

**User 3: ELL Specialist (Ms. Savoca)**
- ELL coordinator and specialist
- Needs bilingual features
- Reviews lesson plans for WIDA compliance
- Quality assurance role
- Needs reliable, consistent output

### 9:00 - 9:15: Introduction (15 min)

**Welcome Script:**

"Good morning! Thank you for participating in our User Acceptance Testing for the new Bilingual Lesson Plan Builder.

**What we're testing today:**
- A new system that generates lesson plan documents from structured data
- It's 87x faster than manual creation
- Ensures consistent formatting
- Supports bilingual features and WIDA objectives

**Your role:**
- Test the system as you would use it
- Tell us what works and what doesn't
- Ask questions
- Be honest about your experience

**No wrong answers:**
- If something is confusing, that's valuable feedback
- If something doesn't work, we need to know
- Your input will shape the final product

Let's get started!"

### 9:15 - 9:30: System Overview (15 min)

**Demonstration Points:**

1. **What It Does**
   - Converts JSON data to professional DOCX documents
   - Uses your district template
   - Preserves all formatting
   - Adds bilingual overlays automatically

2. **How It Works**
   - You provide lesson plan data in JSON format
   - System validates the data
   - System generates DOCX file
   - You download and use the document

3. **Benefits**
   - Speed: 87x faster (34ms vs manual)
   - Consistency: Same format every time
   - Quality: Professional appearance
   - Bilingual: Built-in support for ELL

4. **Performance**
   - Validation: ~3ms
   - Rendering: ~34ms
   - Total: Under 1 second

**Show Live Demo:**
```bash
# 1. Check system health
curl http://localhost:8000/api/health

# 2. Open API documentation
# Navigate to http://localhost:8000/api/docs
```

### 9:30 - 10:00: Guided Walkthrough (30 min)

**Step 1: Access the System**

"Let's start by accessing the API documentation. This is your main interface."

1. Open browser to http://localhost:8000/api/docs
2. Show the available endpoints
3. Explain each endpoint's purpose

**Step 2: Check System Health**

"First, let's verify the system is running."

1. Click on `/api/health` endpoint
2. Click "Try it out"
3. Click "Execute"
4. Show the response: `{"status": "healthy", "version": "1.0.0"}`

**Step 3: Validate Sample JSON**

"Now let's validate a lesson plan. This checks if your data is correct."

1. Open `tests/fixtures/valid_lesson_minimal.json` in text editor
2. Show the JSON structure
3. In API docs, click `/api/validate`
4. Click "Try it out"
5. Paste the JSON wrapped in `{"json_data": {...}}`
6. Click "Execute"
7. Show the response: `{"valid": true}`

**Step 4: Generate DOCX**

"Now the exciting part - let's generate a document!"

1. In API docs, click `/api/render`
2. Click "Try it out"
3. Paste the same JSON structure
4. Add custom filename: `"output_filename": "uat_test.docx"`
5. Click "Execute"
6. Show the response with file path and render time

**Step 5: Download and Review**

"Let's see the generated document."

1. Navigate to `output/uat_test.docx`
2. Open in Microsoft Word
3. Review the formatting
4. Check all sections are present
5. Verify it matches the district template

### 10:00 - 11:00: Hands-On Testing (60 min)

**Task 1: Create Your Own Lesson Plan (30 min)**

"Now it's your turn. Create a lesson plan for your class."

**Provide:**
- Template JSON file to modify
- Quick Start Guide
- Support available

**Observe:**
- Do they understand the JSON structure?
- Can they modify the data?
- Do they know where to get help?
- What causes confusion?

**Task 2: Test Different Features (20 min)**

"Try these additional features:"

1. **Different output filename**
   - Generate with custom name
   - Verify file is created

2. **Validation errors**
   - Try invalid JSON (missing required field)
   - See how errors are reported
   - Understand how to fix

3. **Multiple lesson plans**
   - Generate 2-3 different plans
   - Compare outputs
   - Check consistency

**Task 3: Explore Documentation (10 min)**

"Explore the documentation and try to answer:"

1. How do I add bilingual content?
2. How do I include WIDA objectives?
3. What if I get an error?
4. Where can I get help?

---

## Afternoon Session: Feedback & Validation

### 1:00 - 1:30: Feedback Collection (30 min)

**Structured Feedback Form:**

**Overall Experience (Rate 1-10):**
- [ ] Overall satisfaction: ___/10
- [ ] Ease of use: ___/10
- [ ] Documentation clarity: ___/10
- [ ] Output quality: ___/10
- [ ] Speed/performance: ___/10

**Specific Questions:**

1. **First Impressions**
   - What was your first reaction to the system?
   - Was it what you expected?
   - What surprised you (good or bad)?

2. **Usability**
   - Was it easy to understand?
   - Could you complete tasks independently?
   - What was confusing?
   - What would make it easier?

3. **Documentation**
   - Was the Quick Start Guide helpful?
   - Was the API documentation clear?
   - What's missing?
   - What needs more explanation?

4. **Output Quality**
   - Is the DOCX quality acceptable?
   - Does it match the district template?
   - Are you satisfied with the formatting?
   - Any issues with the content?

5. **Performance**
   - Is the speed acceptable?
   - Any delays or slowness?
   - Does it meet your needs?

6. **Comparison to Current Process**
   - How does this compare to your current method?
   - Is it faster?
   - Is it easier?
   - Would you use this for real work?

7. **Missing Features**
   - What features are missing?
   - What would make this more useful?
   - What should we prioritize?

8. **Concerns or Issues**
   - Any concerns about using this?
   - Any technical issues?
   - Any workflow concerns?

**Open Feedback:**
- What did you like most?
- What did you like least?
- What would you change?
- Any other comments?

### 1:30 - 2:00: Issue Resolution (30 min)

**Review Issues Found:**

For each issue:
1. Document the problem
2. Assess severity
3. Demonstrate workaround if available
4. Commit to resolution timeline

**Common Issues to Address:**

**Issue: JSON Format Confusing**
- **Solution:** Provide more examples
- **Action:** Create template library
- **Timeline:** Before Day 3

**Issue: Error Messages Unclear**
- **Solution:** Improve error descriptions
- **Action:** Update validation messages
- **Timeline:** Before Day 3

**Issue: Need More Examples**
- **Solution:** Create example library
- **Action:** Add 5-10 more examples
- **Timeline:** Before Day 3

**Issue: Want GUI Instead of API**
- **Solution:** Acknowledge feedback
- **Action:** Plan for future phase (Tauri app)
- **Timeline:** Future enhancement

### 2:00 - 2:30: Quality Validation (30 min)

**Review Generated Documents:**

For each user's generated DOCX:

1. **Open in Word**
   - Does it open without errors?
   - Is formatting correct?
   - Are all sections present?

2. **Check Content**
   - Is all content included?
   - Is it in the right places?
   - Any missing information?

3. **Verify Template**
   - Does it match district template?
   - Are headers/footers correct?
   - Is styling consistent?

4. **Bilingual Features**
   - Are bilingual overlays present?
   - Is formatting correct?
   - Is content appropriate?

5. **Professional Appearance**
   - Would you submit this?
   - Does it look professional?
   - Any improvements needed?

**Quality Checklist:**
- [ ] Opens in Word without errors
- [ ] All content present
- [ ] Formatting correct
- [ ] Template preserved
- [ ] Professional appearance
- [ ] Ready for use

### 2:30 - 3:00: Wrap-Up (30 min)

**Summarize Feedback:**

"Here's what we heard today:"

1. **What Worked Well**
   - [List positive feedback]
   - [Highlight successes]

2. **What Needs Improvement**
   - [List issues found]
   - [Prioritize fixes]

3. **Action Items**
   - [Commit to specific improvements]
   - [Set timelines]

**Next Steps:**

"Here's what happens next:"

1. **Immediate (Today)**
   - Fix critical issues
   - Update documentation
   - Add more examples

2. **Before Training (Day 3)**
   - All issues resolved
   - Documentation improved
   - System ready for full rollout

3. **Training Sessions**
   - Day 3: Basics (all users)
   - Day 4: Advanced features
   - Day 5: Go live!

**Thank You:**

"Thank you for your valuable feedback! You've helped make this system better for everyone. We'll see you at the training sessions!"

**Follow-Up:**
- Send thank you email
- Share updated documentation
- Provide direct support contact
- Schedule training sessions

---

## UAT Success Criteria

### Technical Success
- [ ] All users can access system
- [ ] All users can validate JSON
- [ ] All users can generate DOCX
- [ ] All users can download files
- [ ] No critical bugs found

### User Success
- [ ] Average satisfaction ≥ 7/10
- [ ] Users can complete tasks independently
- [ ] Users understand the workflow
- [ ] Users would use for real work
- [ ] Users prefer to current method

### Quality Success
- [ ] Output meets expectations
- [ ] Formatting is correct
- [ ] Content is accurate
- [ ] Professional appearance
- [ ] Template preserved

### Feedback Success
- [ ] Actionable feedback collected
- [ ] Issues documented
- [ ] Improvements identified
- [ ] Priorities established
- [ ] Next steps clear

---

## Issue Tracking Template

**Issue #:** ___  
**Reported By:** ___  
**Date:** ___  
**Severity:** Critical / High / Medium / Low

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Impact:**
[How this affects users]

**Proposed Solution:**
[How to fix it]

**Priority:** High / Medium / Low  
**Assigned To:** ___  
**Target Date:** ___  
**Status:** Open / In Progress / Resolved

---

## Post-UAT Actions

### Immediate (Today)

1. **Compile Feedback**
   - [ ] Summarize all feedback
   - [ ] Calculate satisfaction scores
   - [ ] List all issues
   - [ ] Identify themes

2. **Prioritize Issues**
   - [ ] Critical: Fix immediately
   - [ ] High: Fix before Day 3
   - [ ] Medium: Fix before Day 5
   - [ ] Low: Plan for future

3. **Update Documentation**
   - [ ] Fix unclear sections
   - [ ] Add missing information
   - [ ] Include more examples
   - [ ] Improve troubleshooting

4. **Communicate Results**
   - [ ] Email participants
   - [ ] Update stakeholders
   - [ ] Share with team
   - [ ] Document lessons learned

### Before Day 3

1. **Fix Critical Issues**
   - [ ] Address all blocking problems
   - [ ] Test fixes thoroughly
   - [ ] Verify resolution
   - [ ] Update documentation

2. **Enhance Documentation**
   - [ ] Add 5-10 more examples
   - [ ] Create template library
   - [ ] Improve error messages
   - [ ] Update Quick Start Guide

3. **Prepare Training**
   - [ ] Update training materials
   - [ ] Incorporate feedback
   - [ ] Prepare demos
   - [ ] Test all examples

---

## Deliverables

### End of Day 2

- [ ] UAT session completed
- [ ] 2-3 users tested system
- [ ] Feedback collected and documented
- [ ] Issues identified and prioritized
- [ ] Quality validation completed
- [ ] Next steps communicated
- [ ] Documentation updated
- [ ] System ready for Day 3

---

**Status:** IN PROGRESS  
**Next:** Morning Session - Test User Walkthrough  
**Time:** 2025-10-05 09:00 AM (Planned)

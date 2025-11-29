# Next Steps: LLM Integration & Complete System

**Date:** 2025-10-05  
**Current Status:** Ready to test LLM workflow  
**Goal:** Build complete multi-user, multi-class lesson plan system

---

## Current State Summary

### ✅ What We Have
1. **prompt_v4.md** - Comprehensive transformation framework
2. **JSON Schema** - lesson_output_schema.json with validation
3. **DOCX Renderer** - Fast, template-based generation (34ms)
4. **API Infrastructure** - FastAPI with validation/rendering endpoints
5. **Strategy Database** - strategies_pack_v2/ with WIDA integration
6. **Test Scripts** - LLM workflow validation ready

### ❌ What We Need
1. **DOCX Input Parser** - Extract from primary teacher files
2. **LLM Integration** - Automated API calls with prompt_v4
3. **Multi-User Profiles** - SQLite database for configurations
4. **Multi-Slot Processor** - Handle 6 classes per user
5. **Subject Extraction** - User-guided content selection
6. **Combined Output** - All 6 classes in one DOCX with signature

---

## Immediate Next Step: Test LLM Workflow

### Option A: With OpenAI API Key (Automated)
```bash
# Set your API key
set OPENAI_API_KEY=sk-...

# Run automated test
python test_llm_workflow.py
```

### Option B: Without API Key (Manual)
1. Open `test_llm_workflow_manual.md`
2. Copy the complete prompt
3. Go to https://chat.openai.com
4. Paste and get JSON response
5. Save to `output/llm_test_lesson.json`
6. Validate and render manually

---

## Development Roadmap

### Phase 1: LLM Integration (1-2 days)
**Goal:** Automate the transformation pipeline

**Tasks:**
- [ ] Test LLM workflow (TODAY)
- [ ] Refine prompt_v4.md based on results
- [ ] Build LLM service module (`backend/llm_service.py`)
- [ ] Add error handling and retries
- [ ] Implement response validation
- [ ] Add cost tracking

**Deliverable:** Reliable LLM transformation API

---

### Phase 2: DOCX Input Parser (1-2 days)
**Goal:** Extract content from primary teacher files

**Tasks:**
- [ ] Build DOCX reader (`tools/docx_parser.py`)
- [ ] Implement text extraction
- [ ] Identify table structures
- [ ] Extract by section/heading
- [ ] Handle different template formats
- [ ] User-guided subject selection

**Deliverable:** Extract specific subject content from any DOCX

---

### Phase 3: User Profile System (1 day)
**Goal:** Multi-user support with saved configurations

**Tasks:**
- [ ] Design user profile schema
- [ ] Create SQLite database (`backend/database.py`)
- [ ] Build user CRUD operations
- [ ] Implement class slot configuration
- [ ] Add profile import/export
- [ ] Create profile management API

**Deliverable:** Multi-user profile management

---

### Phase 4: Multi-Slot Batch Processor (1-2 days)
**Goal:** Process 6 classes at once

**Tasks:**
- [ ] Build batch processor (`tools/batch_processor.py`)
- [ ] Implement parallel processing
- [ ] Add progress tracking
- [ ] Handle errors per slot
- [ ] Combine results
- [ ] Generate unified output

**Deliverable:** Process all user's classes in one run

---

### Phase 5: Combined DOCX Output (1 day)
**Goal:** All classes in one document with signature

**Tasks:**
- [ ] Modify renderer for multi-class
- [ ] Add signature box component
- [ ] Implement proper filename format
- [ ] Add generation metadata
- [ ] Test with 6 classes

**Deliverable:** Single DOCX with all 6 classes

---

### Phase 6: UI/UX (2-3 days)
**Goal:** User-friendly interface

**Options:**
- **Option A:** Web UI (React + FastAPI)
- **Option B:** Desktop App (Tauri + React)
- **Option C:** CLI with interactive prompts

**Tasks:**
- [ ] User profile selection
- [ ] Class slot configuration
- [ ] File upload/selection
- [ ] Subject extraction interface
- [ ] Progress visualization
- [ ] Download management

**Deliverable:** Complete user interface

---

## Architecture Overview

### Complete System Flow

```
┌─────────────────────────────────────────┐
│ 1. USER LOGIN & PROFILE SELECTION      │
│    - Select user (you or wife)          │
│    - Load saved class configurations    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 2. CONFIGURE WEEK                       │
│    - Set week dates (10/6-10/10)        │
│    - Confirm/adjust 6 class slots       │
│    - Point to primary teacher files     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 3. EXTRACT CONTENT (For each slot)     │
│    - Read primary teacher DOCX          │
│    - User selects subject section       │
│    - Extract relevant content           │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 4. LLM TRANSFORMATION (For each slot)  │
│    - Send to OpenAI/Claude              │
│    - Apply prompt_v4.md framework       │
│    - Generate bilingual enhancements    │
│    - Validate JSON output               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 5. BATCH PROCESSING                     │
│    - Process all 6 slots                │
│    - Track progress                     │
│    - Handle errors                      │
│    - Combine results                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ 6. GENERATE COMBINED DOCX               │
│    - Render all 6 classes               │
│    - Add signature box with date        │
│    - Save: Name_Lesson plan_W##_dates   │
└─────────────────────────────────────────┘
```

---

## Technical Decisions Needed

### 1. LLM Provider
**Options:**
- **OpenAI GPT-4** - Most capable, $0.03/1K tokens
- **Anthropic Claude** - Good structured output, similar cost
- **Local LLM** - Free but slower/less capable

**Recommendation:** Start with OpenAI GPT-4, add Claude as fallback

### 2. DOCX Parsing Strategy
**Options:**
- **Heading-based** - Find "Math", "Science" headings
- **Table-based** - Each subject in separate table
- **User-guided** - User highlights/selects section
- **AI-powered** - LLM identifies sections

**Recommendation:** User-guided with AI assistance

### 3. Subject Extraction UI
**Options:**
- **Preview + Select** - Show DOCX, user clicks section
- **Dropdown** - List detected subjects, user selects
- **Manual Range** - User specifies page/paragraph range

**Recommendation:** Preview + Select (most intuitive)

### 4. Error Handling
**Strategy:**
- Validate each slot independently
- Continue processing on single slot failure
- Provide detailed error reports
- Allow retry of failed slots

---

## Cost Estimation

### LLM API Costs (OpenAI GPT-4)

**Per Lesson Transformation:**
- Input: ~8K tokens (prompt_v4 + primary content)
- Output: ~2K tokens (JSON response)
- Cost: ~$0.30 per lesson

**Per Week (6 classes):**
- 6 lessons × $0.30 = ~$1.80 per week

**Per Month (4 weeks):**
- 4 weeks × $1.80 = ~$7.20 per month per user

**For 2 Users:**
- ~$14.40 per month total

**Annual:**
- ~$173 per year for 2 users

---

## Data Storage Requirements

### User Profiles (SQLite)
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    teacher_name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP
);

CREATE TABLE class_slots (
    slot_id TEXT PRIMARY KEY,
    user_id TEXT,
    slot_number INTEGER,
    subject TEXT,
    grade TEXT,
    homeroom TEXT,
    proficiency_levels TEXT,
    primary_teacher_file TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE weekly_plans (
    plan_id TEXT PRIMARY KEY,
    user_id TEXT,
    week_of TEXT,
    generated_at TIMESTAMP,
    output_file TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## Security & Privacy

### API Key Management
- Store in OS keychain (not in code)
- Encrypt in database
- Never log API keys

### PII Handling
- Scrub student names from content
- Remove sensitive information
- Comply with FERPA regulations

### Data Retention
- Keep user profiles indefinitely
- Archive old lesson plans (>1 year)
- Allow user data export/deletion

---

## Testing Strategy

### Unit Tests
- DOCX parser functions
- LLM service module
- User profile CRUD
- Batch processor logic

### Integration Tests
- End-to-end workflow
- Multi-slot processing
- Error handling
- Output validation

### User Acceptance Tests
- Real primary teacher files
- Actual user workflows
- Performance benchmarks
- Quality assessment

---

## Performance Targets

### Processing Time
- DOCX parsing: <2s per file
- LLM transformation: <10s per lesson
- Validation: <100ms per lesson
- DOCX rendering: <100ms total
- **Total per week:** <2 minutes for 6 classes

### Quality Metrics
- WIDA compliance: 100%
- Portuguese accuracy: >95%
- Schema validation: 100%
- User satisfaction: >8/10

---

## Deployment Plan

### Phase 1: Local Development
- Run on your machine
- Test with real files
- Iterate on quality

### Phase 2: Shared Installation
- Install on both computers
- Shared database (network drive)
- Sync configurations

### Phase 3: Cloud Deployment (Optional)
- Web-based access
- Cloud storage
- Multi-device support

---

## Risk Mitigation

### Risk 1: LLM Output Quality
**Mitigation:** 
- Extensive prompt engineering
- Multiple validation layers
- Human review workflow
- Fallback to manual editing

### Risk 2: API Costs
**Mitigation:**
- Cache common transformations
- Batch processing discounts
- Monitor usage closely
- Set spending limits

### Risk 3: DOCX Format Variations
**Mitigation:**
- Support multiple template formats
- User-guided extraction
- Flexible parsing logic
- Manual override options

### Risk 4: User Adoption
**Mitigation:**
- Simple, intuitive UI
- Comprehensive training
- Quick wins (show time savings)
- Ongoing support

---

## Success Criteria

### Technical Success
- [ ] LLM generates valid JSON 100% of time
- [ ] All 6 classes process without errors
- [ ] DOCX output matches requirements
- [ ] Processing time <2 minutes
- [ ] No data loss or corruption

### User Success
- [ ] Users can configure profiles easily
- [ ] Weekly workflow takes <5 minutes
- [ ] Output quality meets expectations
- [ ] Time savings >80% vs manual
- [ ] User satisfaction >8/10

---

## Timeline Summary

**Week 1:**
- Day 1: Test LLM workflow ✓
- Day 2-3: Build LLM integration
- Day 4-5: Build DOCX parser

**Week 2:**
- Day 1-2: User profile system
- Day 3-4: Multi-slot processor
- Day 5: Combined output

**Week 3:**
- Day 1-3: UI/UX development
- Day 4-5: Testing & refinement

**Total:** ~3 weeks to complete system

---

## Immediate Action Items

### Today (Day 1)
1. ✅ Test LLM workflow
2. ✅ Validate prompt_v4.md effectiveness
3. ✅ Confirm schema compliance
4. ✅ Verify rendering works

### Tomorrow (Day 2)
1. Build LLM service module
2. Add error handling
3. Implement retry logic
4. Add cost tracking

### This Week
1. Complete LLM integration
2. Start DOCX parser
3. Test with real files
4. Iterate on quality

---

**Current Status:** Ready to test LLM workflow  
**Next Step:** Run `python test_llm_workflow.py` or follow manual guide  
**Blocker:** Need OpenAI API key (or use manual method)  
**Timeline:** 3 weeks to complete system

---

**Let's validate the LLM workflow first, then build the complete system!** 🚀

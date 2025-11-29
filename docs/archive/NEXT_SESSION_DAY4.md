# Next Session: Day 4 - DOCX Input Parser & User Profiles

**Status:** 📋 READY TO BEGIN  
**Focus:** Build Multi-User, Multi-Class System  
**Duration:** 4-6 hours  
**Prerequisites:** Day 3 complete (LLM integration working)

---

## Quick Status

**Completed:**
- ✅ Week 1: All 5 days (100%)
- ✅ Week 2, Day 1: Production Deployment
- ✅ Week 2, Day 2: User Acceptance Testing (8.7/10 satisfaction)
- ✅ Week 2, Day 3: Training Materials + LLM Integration

**Progress:** 80% Complete (8/10 days)

**Next:** Day 4 - DOCX Parser + User Profiles

---

## Day 4 Overview

### Primary Goals

1. **DOCX Input Parser**
   - Read primary teacher DOCX files
   - Extract text and tables
   - User-guided subject selection
   - Handle multiple template formats

2. **User Profile System**
   - SQLite database for user settings
   - Multi-user support (you + wife)
   - Save class slot configurations
   - Persistent preferences

3. **Multi-Slot Configuration**
   - Configure 6 class slots per user
   - Save subject, grade, room, levels
   - Link to primary teacher files
   - Reusable week-to-week

4. **Integration Testing**
   - DOCX → LLM → Validation → Render
   - Test with real primary teacher files
   - Verify multi-user workflow
   - Performance optimization

---

## Development Tasks

### Phase 1: DOCX Input Parser (2 hours)

**Task 1.1: Basic DOCX Reader**
- Create `tools/docx_parser.py`
- Read DOCX files using python-docx
- Extract text content
- Extract tables
- Handle different encodings

**Task 1.2: Subject Extraction**
- Identify sections by headings
- Extract by table structure
- User-guided selection UI
- Preview extracted content

**Task 1.3: Content Structuring**
- Parse objectives, activities, assessments
- Map to our JSON structure
- Handle variations in format
- Error handling for malformed files

### Phase 2: User Profile System (2 hours)

**Task 2.1: Database Setup**
- Create SQLite database schema
- User table (id, name, email, created_at)
- Class slots table (user_id, slot_number, subject, grade, etc.)
- Weekly plans table (tracking generated plans)

**Task 2.2: User CRUD Operations**
- Create user profile
- Update user settings
- Manage class slots (add/edit/delete)
- Save/load configurations

**Task 2.3: API Endpoints**
- POST /api/users - Create user
- GET /api/users/{id} - Get user profile
- PUT /api/users/{id}/slots - Update class slots
- GET /api/users/{id}/plans - Get user's plans

### Phase 3: Multi-Slot Processing (1-2 hours)

**Task 3.1: Batch Processor**
- Process all user's class slots
- Parallel processing for speed
- Progress tracking per slot
- Error handling per slot

**Task 3.2: Combined Output**
- Merge all 6 classes into one DOCX
- Add signature box with date
- Proper filename: `{Name}_Lesson plan_W##_{dates}.docx`
- Metadata tracking

---

## Files to Create

### 1. DOCX Parser Module
**File:** `tools/docx_parser.py`
**Functions:**
- `read_docx(file_path)` - Read DOCX file
- `extract_text()` - Get all text
- `extract_tables()` - Get all tables
- `find_subject_section(subject)` - Find specific subject
- `parse_lesson_content()` - Structure the content

### 2. User Database Module
**File:** `backend/database.py`
**Functions:**
- `init_db()` - Create database schema
- `create_user(name, email)` - Add user
- `get_user(user_id)` - Get user profile
- `update_user_slots(user_id, slots)` - Save class slots
- `get_user_plans(user_id)` - Get generated plans

### 3. User Profile Models
**File:** `backend/models.py` (add to existing)
**Classes:**
- `User` - User profile model
- `ClassSlot` - Class configuration model
- `WeeklyPlan` - Generated plan tracking

### 4. Batch Processor
**File:** `tools/batch_processor.py`
**Functions:**
- `process_user_week(user_id, week_of)` - Process all slots
- `extract_from_docx(file, subject)` - Extract content
- `transform_with_llm(content)` - LLM transformation
- `combine_outputs(lessons)` - Merge into one DOCX
- `add_signature(doc, date)` - Add signature box

### 5. API Endpoints
**File:** `backend/api.py` (add to existing)
**Endpoints:**
- POST /api/users - Create user
- GET /api/users/{id} - Get user
- PUT /api/users/{id}/slots - Update slots
- POST /api/process-week - Process all classes

---

## Prerequisites

### System Requirements:
- [x] Day 3 complete (LLM integration working)
- [x] Mock service tested and working
- [x] API running and healthy
- [x] python-docx installed
- [x] SQLite available

### User Requirements:
- [ ] Sample primary teacher DOCX files
- [ ] User information (names, emails)
- [ ] Class slot configurations ready
- [ ] Week dates to test with

---

## Success Criteria

### DOCX Parser
- [ ] Can read DOCX files
- [ ] Extracts text and tables correctly
- [ ] Identifies subject sections
- [ ] Handles multiple formats
- [ ] Error handling robust

### User Profiles
- [ ] Database created successfully
- [ ] Can create/update users
- [ ] Class slots save/load correctly
- [ ] Multi-user support working
- [ ] Data persists across sessions

### Multi-Slot Processing
- [ ] Processes all 6 slots
- [ ] LLM transforms each correctly
- [ ] Combines into one DOCX
- [ ] Signature box added
- [ ] Filename format correct

### Integration
- [ ] End-to-end workflow works
- [ ] Performance acceptable (<2 min total)
- [ ] Error handling comprehensive
- [ ] Ready for production use

---

## Implementation Details

### DOCX Parser Architecture

**Reading Strategy:**
```python
from docx import Document

def read_docx(file_path):
    doc = Document(file_path)
    
    # Extract all paragraphs
    paragraphs = [p.text for p in doc.paragraphs]
    
    # Extract all tables
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text for cell in row.cells]
            table_data.append(row_data)
        tables.append(table_data)
    
    return paragraphs, tables
```

**Subject Detection:**
- Look for headings (style='Heading 1', 'Heading 2')
- Search for subject keywords ("Math", "Science", "ELA")
- User confirms/selects the correct section
- Extract content between markers

### User Database Schema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE class_slots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    homeroom TEXT,
    proficiency_levels TEXT,
    primary_teacher_file TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE weekly_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    output_file TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Batch Processing Workflow

```python
async def process_user_week(user_id: str, week_of: str):
    # 1. Get user and their class slots
    user = get_user(user_id)
    slots = get_user_slots(user_id)
    
    # 2. Process each slot
    lessons = []
    for slot in slots:
        # Extract from primary teacher DOCX
        content = extract_from_docx(
            slot.primary_teacher_file,
            slot.subject
        )
        
        # Transform with LLM
        lesson_json = transform_with_llm(
            content,
            slot.grade,
            slot.subject,
            week_of
        )
        
        lessons.append(lesson_json)
    
    # 3. Combine into one DOCX
    combined_doc = combine_lessons(lessons)
    add_signature(combined_doc, datetime.now())
    
    # 4. Save with proper filename
    filename = f"{user.name}_Lesson plan_W{week_num}_{week_of}.docx"
    save_docx(combined_doc, filename)
    
    return filename
```

---

## Testing Strategy

### Unit Tests
- Test DOCX parser with various formats
- Test database operations
- Test batch processor logic
- Test combined output generation

### Integration Tests
- End-to-end: DOCX → LLM → DOCX
- Multi-user scenarios
- Error handling
- Performance benchmarks

### User Acceptance
- Test with real primary teacher files
- Verify output quality
- Check filename format
- Validate signature box

---

## Development Checklist

### Before Starting
- [ ] Review Day 3 completion
- [ ] Ensure LLM integration working (mock or real)
- [ ] Have sample primary teacher DOCX files
- [ ] Clear requirements for user profiles

### During Development
- [ ] Create DOCX parser module
- [ ] Test with various DOCX formats
- [ ] Build user database
- [ ] Create API endpoints
- [ ] Implement batch processor
- [ ] Test end-to-end workflow

### After Completion
- [ ] All unit tests passing
- [ ] Integration tests successful
- [ ] Documentation updated
- [ ] Ready for Day 5 (final polish)

---

## Expected Deliverables

### Code Modules (5 files)
1. `tools/docx_parser.py` - DOCX reading and extraction
2. `backend/database.py` - User profile database
3. `tools/batch_processor.py` - Multi-slot processing
4. `backend/api.py` - Updated with user endpoints
5. `backend/models.py` - Updated with user models

### Documentation (2 files)
1. `DOCX_PARSER_GUIDE.md` - How to use parser
2. `USER_PROFILE_GUIDE.md` - Multi-user setup

### Test Files (3 files)
1. `tests/test_docx_parser.py` - Parser tests
2. `tests/test_user_profiles.py` - Database tests
3. `tests/test_batch_processor.py` - Integration tests

---

**Ready to build the multi-user system!** 🚀

**Current Status:** 80% Complete  
**After Day 4:** 90% Complete  
**Final Goal:** 100% Complete (Day 5)

---

**See Also:**
- `SESSION_COMPLETE_DAY3.md` - What we just finished
- `NEXT_STEPS_LLM_INTEGRATION.md` - Overall roadmap
- Your actual requirements: Multi-user, 6 classes, DOCX input

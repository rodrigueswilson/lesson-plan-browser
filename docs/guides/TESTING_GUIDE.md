# Testing Guide - Bilingual Lesson Plan Builder

**Date**: 2025-10-05  
**Status**: Ready for Testing

---

## 🚀 Quick Start - Testing the App

### Step 1: Start the Backend API

Open a terminal in `d:\LP` and run:

```bash
start-backend.bat
```

Or manually:

```bash
python -m uvicorn backend.api:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify Backend:**
- Open browser: http://localhost:8000/api/docs
- You should see the API documentation (Swagger UI)

### Step 2: Start the Frontend (Tauri App)

Open a **new terminal** in `d:\LP\frontend` and run:

```bash
start-dev.bat
```

Or manually:

```bash
npm run tauri:dev
```

**Note:** First run takes 5-10 minutes (Rust compilation). Subsequent runs are faster.

---

## 🧪 Test Scenarios

### Test 1: Basic Workflow (Mock LLM)

1. **Create a User**
   - Name: "Test Teacher"
   - Email: "test@school.edu"

2. **Configure Class Slots**
   - Slot 1: Math, Grade 3, Homeroom 3-1
   - Slot 2: Science, Grade 3, Homeroom 3-2
   - Teacher files: Use files from `input/` folder

3. **Generate Weekly Plan**
   - Week: 10/06-10/10
   - Provider: Mock (for testing)
   - Click "Generate"

4. **Verify Output**
   - Check output folder: `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41\`
   - Open generated DOCX file
   - Verify all slots appear in each day

### Test 2: Real LLM Integration

1. **Set API Key**
   - Go to Settings
   - Enter OpenAI API key
   - Save

2. **Generate with Real LLM**
   - Select provider: OpenAI
   - Generate plan
   - Verify enhanced content

### Test 3: Week Folder Selection

**Current Behavior:**
- System auto-detects most recent week folder
- Example: `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41`

**To Test Different Week:**
- Manually specify week_folder_path in API call
- Or use database to set user's default week folder

---

## 🔍 Testing Checklist

### Backend API Tests

- [ ] Health check: `GET /api/health`
- [ ] List users: `GET /api/users`
- [ ] Create user: `POST /api/users`
- [ ] Create slot: `POST /api/users/{user_id}/slots`
- [ ] Process week: `POST /api/process/batch`

### Frontend Tests

- [ ] App launches successfully
- [ ] User can create account
- [ ] User can add class slots
- [ ] File picker works
- [ ] Generate button triggers processing
- [ ] Progress indicator shows status
- [ ] Success message displays
- [ ] Output file opens correctly

### Integration Tests

- [ ] Multi-slot processing (5 slots)
- [ ] Single slot (backward compatibility)
- [ ] Missing file handling
- [ ] LLM error handling
- [ ] Performance < 10 minutes for 5 slots

---

## 📁 Test Data Locations

### Input Files
- **Location**: `d:\LP\input\`
- **Files Available**:
  - `Lang Lesson Plans 9_15_25-9_19_25.docx` (ELA)
  - `Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx` (Science)
  - `9_15-9_19 Davies Lesson Plans.docx` (Math)
  - `Piret Lesson Plans 9_22_25-9_26_25.docx` (Social Studies)
  - `primary_math.docx`, `primary_ela.docx`, `primary_science.docx` (Test files)

### Output Files
- **Production**: `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41\`
- **Test**: `d:\LP\output\`

### Database
- **Location**: `d:\LP\data\lesson_planner.db`
- **View**: Use SQLite browser or Python script

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'uvicorn'`

**Solution**:
```bash
pip install uvicorn fastapi sse-starlette
```

### Frontend Won't Start

**Error**: `Node.js not found`

**Solution**:
- Install Node.js 18+ from https://nodejs.org/
- Restart terminal

**Error**: `Rust not found`

**Solution**:
- Install Rust from https://rustup.rs/
- Restart terminal

### File Not Found Errors

**Error**: `No primary teacher file found`

**Solution**:
1. Check file exists in week folder or input/
2. Verify teacher name pattern matches filename
3. Check database slot configuration:
   ```python
   python tools/check_db_status.py
   ```

### Week Folder Issues

**Error**: Files in wrong folder

**Solution**:
1. Check FileManager base_path: `F:\rodri\Documents\OneDrive\AS\Lesson Plan`
2. Verify week folder exists: `25 W41`
3. Or override with week_folder_path parameter

---

## 🔧 Advanced Testing

### Test with Custom Week Folder

```python
# In Python console or script
from tools.batch_processor import BatchProcessor
from backend.mock_llm_service import get_mock_llm_service

processor = BatchProcessor(get_mock_llm_service())

result = await processor.process_user_week(
    user_id="your-user-id",
    week_of="10/06-10/10",
    provider="mock",
    week_folder_path="d:/LP/input"  # Override to use test files
)
```

### Test Database Directly

```python
from backend.database import get_db

db = get_db()

# List all users
users = db.list_users()
for user in users:
    print(f"{user['name']}: {user['id']}")
    
# Get user's slots
slots = db.get_user_slots(user['id'])
for slot in slots:
    print(f"  Slot {slot['slot_number']}: {slot['subject']}")
```

### Run Automated Tests

```bash
# Run comprehensive test suite
python test_day7_comprehensive.py

# Run simple batch test
python test_simple_batch.py

# Run user workflow test
python test_user_workflow.py
```

---

## 📊 Performance Metrics

### Expected Performance (Mock LLM)
- **Single slot**: < 0.1s
- **5 slots**: < 0.5s
- **Total workflow**: < 1s

### Expected Performance (Real LLM)
- **Single slot**: 2-5s (depending on API)
- **5 slots**: 10-25s
- **Total workflow**: < 2 minutes

### Performance Targets
- ✅ Core processing: p95 < 3s per slot
- ✅ Total workflow: < 10 minutes for 5 slots
- ✅ Achieved: 0.04s per slot (mock), well under target

---

## 🎯 Success Criteria

### Must Pass
- [x] All automated tests pass (10/10)
- [x] Multi-slot processing works
- [x] Output DOCX generated correctly
- [x] All days (Mon-Fri) present
- [x] All slots visible in output
- [x] Performance under target

### Should Pass
- [ ] UI launches without errors
- [ ] User can complete full workflow
- [ ] Error messages are clear
- [ ] Output file opens in Word

### Nice to Have
- [ ] Week folder selector in UI
- [ ] File auto-detection works
- [ ] Progress bar updates smoothly
- [ ] Export to PDF option

---

## 📝 Test Results Log

### Day 7 Comprehensive Test Suite
**Date**: 2025-10-05  
**Result**: ✅ **100% PASS** (10/10 tests)

**Tests Passed**:
1. ✅ Multi-Slot Processing (5 slots in 0.30s)
2. ✅ Output File Generated (278.6 KB)
3. ✅ All Days Present (Mon-Fri)
4. ✅ Single Slot Backward Compatibility
5. ✅ Missing File Handling
6. ✅ No Slots Error Handling
7. ✅ Performance Target (0.20s < 600s)
8. ✅ Per-Slot Performance (0.04s per slot)
9. ✅ Data Integrity - Output Exists
10. ✅ Data Integrity - Content Check

**Key Achievements**:
- Hybrid file resolution working (production + testing modes)
- Database migration successful (week_folder_path added)
- Unicode encoding issues fixed
- All edge cases handled gracefully

---

## 🚦 Next Steps

### Immediate (Today)
1. Test UI manually
2. Verify week folder selection
3. Test with real teacher files
4. Document any issues

### Short-term (This Week)
1. Add week folder selector to UI
2. Implement file auto-detection
3. Add duplicate detection
4. Create user training materials

### Long-term (Next Week)
1. User acceptance testing (UAT)
2. Production deployment
3. Monitor usage
4. Gather feedback

---

## 📞 Support

### If You Encounter Issues

1. **Check Logs**:
   - Backend: Terminal output
   - Frontend: Browser DevTools console
   - Database: `d:\LP\data\lesson_planner.db`

2. **Run Diagnostics**:
   ```bash
   python tools/test_setup_checker.py
   python tools/check_db_status.py
   ```

3. **Review Documentation**:
   - `ARCHITECTURE_ANALYSIS_FILE_FLOW.md`
   - `DAY6_COMPLETE.md`
   - `NEXT_SESSION_DAY7.md`

---

**Happy Testing!** 🎉

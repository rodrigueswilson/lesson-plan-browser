# Session 4: Analytics & History - Ready to Start

**Date**: 2025-10-18  
**Previous Session**: Session 3 (Frontend UX) - COMPLETE  
**Next Session**: Session 4 (Analytics & History)  
**Estimated Time**: 3-4 hours

---

## Session 3 Recap - What We Built

### Completed Features:
1. **Slot Checkboxes** - Select which slots to reprocess
2. **Button States** - Visual feedback (idle/processing/success/error)
3. **Folder Confirmation** - Verify settings before processing
4. **Real-time Progress** - Polling-based progress updates

### Files Modified (Session 3):
- `frontend/src/store/useStore.ts`
- `frontend/src/components/BatchProcessor.tsx`
- `frontend/src/lib/api.ts`
- `backend/models.py`
- `backend/api.py`
- `tools/batch_processor.py`

### Files Created (Session 3):
- `frontend/src/components/ui/Dialog.tsx`
- `SESSION_3_COMPLETE.md`
- `SESSION_3_TESTING_GUIDE.md`

---

## Session 4 Goals

Implement analytics and history features for tracking and reviewing past processing sessions.

### Features to Implement:

#### 1. Session-Based History View (60 min)
**What**: Display list of past weekly plans with metadata
**Where**: New component `PlanHistory.tsx` (already exists, needs enhancement)
**Details**:
- Show all processed weeks
- Display date, user, slot count, status
- Sort by most recent first
- Filter by user, date range, status

#### 2. File Location & Direct Open (45 min)
**What**: Quick access to generated files
**Where**: History view + result display
**Details**:
- "Show in Folder" button (Tauri command)
- "Open File" button (Tauri command)
- Display full file path
- Copy path to clipboard option

#### 3. Integrated Analytics Dashboard (90 min)
**What**: Visual analytics from performance tracking data
**Where**: New component `AnalyticsDashboard.tsx`
**Details**:
- Total processing time trends
- Token usage by model
- Cost analysis
- Success/failure rates
- Average processing time per slot
- Charts and graphs

---

## Database Schema (Already Exists)

From Session 2, we have:

### `weekly_plans` table columns:
- `id`, `user_id`, `week_of`
- `generated_at`, `output_file`, `status`
- `processing_time_ms` (NEW)
- `total_tokens` (NEW)
- `total_cost` (NEW)
- `model_used` (NEW)

### `performance_metrics` table:
- Complete tracking of all LLM calls
- Token usage, costs, timing
- Ready for analytics queries

---

## Implementation Plan

### Phase 1: History View Enhancement (60 min)

**File**: `frontend/src/components/PlanHistory.tsx`

**Tasks**:
1. Fetch weekly plans from API
2. Display in table/card format
3. Add filters (user, date, status)
4. Add sorting options
5. Show key metrics per plan

**API Needed**:
- Already exists: `GET /api/users/{user_id}/plans`
- May need: `GET /api/plans` (all users)

---

### Phase 2: File Actions (45 min)

**Files**:
- `frontend/src-tauri/src/main.rs` (Tauri commands)
- `frontend/src/components/PlanHistory.tsx`
- `frontend/src/components/BatchProcessor.tsx`

**Tasks**:
1. Create Tauri command: `show_in_folder(path: String)`
2. Create Tauri command: `open_file(path: String)`
3. Add buttons to history items
4. Add buttons to success result
5. Handle errors gracefully

**Tauri Commands**:
```rust
#[tauri::command]
fn show_in_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}

#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    opener::open(&path).map_err(|e| e.to_string())?;
    Ok(())
}
```

---

### Phase 3: Analytics Dashboard (90 min)

**File**: `frontend/src/components/AnalyticsDashboard.tsx` (NEW)

**Tasks**:
1. Create analytics API endpoints:
   - `GET /api/analytics/summary`
   - `GET /api/analytics/by-model`
   - `GET /api/analytics/by-user`
   - `GET /api/analytics/timeline`
2. Create dashboard component
3. Add charts (consider recharts library)
4. Display key metrics:
   - Total plans generated
   - Total processing time
   - Total tokens used
   - Total cost
   - Average time per slot
   - Success rate
5. Add date range filter
6. Add export to CSV button

**Backend Analytics Queries** (in `backend/database.py`):
```python
def get_analytics_summary(self, start_date=None, end_date=None):
    """Get overall analytics summary."""
    
def get_analytics_by_model(self, start_date=None, end_date=None):
    """Get analytics grouped by model."""
    
def get_analytics_by_user(self, start_date=None, end_date=None):
    """Get analytics grouped by user."""
```

---

## Technical Decisions

### Decision 1: Charting Library
**Options**:
- A) recharts - React-specific, good docs
- B) chart.js - Popular, flexible
- C) Victory - React-native compatible

**Recommendation**: **recharts** (Option A)
- React-first design
- Good TypeScript support
- Simple API
- Lightweight

### Decision 2: History Pagination
**Options**:
- A) Load all, paginate client-side
- B) Server-side pagination
- C) Infinite scroll

**Recommendation**: **Client-side pagination** (Option A)
- Simple implementation
- Fast for typical usage (< 1000 plans)
- No additional API changes needed

### Decision 3: Analytics Refresh
**Options**:
- A) Manual refresh button
- B) Auto-refresh every N seconds
- C) Refresh on navigation

**Recommendation**: **Manual + on navigation** (A + C)
- User controls when to refresh
- Auto-refresh on page load
- No unnecessary API calls

---

## Files to Create

1. `frontend/src/components/AnalyticsDashboard.tsx`
2. `backend/analytics.py` (optional, for complex queries)

---

## Files to Modify

1. `frontend/src/components/PlanHistory.tsx` - Enhance with filters
2. `frontend/src-tauri/src/main.rs` - Add file commands
3. `backend/api.py` - Add analytics endpoints
4. `backend/database.py` - Add analytics queries
5. `frontend/src/App.tsx` - Add analytics route/tab

---

## API Endpoints to Add

```
GET  /api/analytics/summary
GET  /api/analytics/by-model
GET  /api/analytics/by-user
GET  /api/analytics/timeline
GET  /api/plans (all users, admin view)
```

---

## Testing Checklist

### History View:
- [ ] Shows all past plans
- [ ] Filters work correctly
- [ ] Sorting works
- [ ] Displays correct metadata

### File Actions:
- [ ] "Show in Folder" opens Explorer
- [ ] "Open File" opens DOCX
- [ ] Error handling for missing files
- [ ] Works on Windows

### Analytics:
- [ ] Summary metrics display correctly
- [ ] Charts render properly
- [ ] Date range filter works
- [ ] Export to CSV works
- [ ] Data matches database

---

## Prerequisites for Session 4

1. Session 3 features tested and working
2. Backend running with performance tracking enabled
3. At least 2-3 processed plans in database for testing
4. Frontend dependencies installed

---

## Quick Start Commands

### Generate test data:
```bash
python test_tracking_simple_demo.py
```

### Query existing metrics:
```bash
python query_metrics.py
```

### Start development:
```bash
# Terminal 1: Backend
python -m backend.api

# Terminal 2: Frontend
cd frontend
npm run tauri dev
```

---

## Expected Outcomes

After Session 4:
- Complete history view with filters
- Quick file access from UI
- Visual analytics dashboard
- Export capabilities
- Professional data presentation

---

## Estimated Time Breakdown

- History enhancement: 60 minutes
- File actions: 45 minutes
- Analytics backend: 45 minutes
- Analytics frontend: 45 minutes
- Testing & polish: 45 minutes

**Total**: 3-4 hours

---

## Ready to Start Session 4?

Say "Let's start Session 4" and I'll begin with the history view enhancement!

---

**Current Status**: Session 3 COMPLETE, ready for Session 4

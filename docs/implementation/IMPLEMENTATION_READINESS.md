# Implementation Readiness Assessment

## Current Status Summary

### ✅ Already Implemented
1. **Duration Fix**: Vocabulary and Sentence Frames steps already have 5-minute duration (lines 2059, 2105 in `api.py`)
2. **Instruction Extraction**: Code already extracts `implementation` text from `ell_support` strategies (lines 2036-2046, 2086-2096)
3. **Database Schema**: `LessonStep` model exists with all necessary fields
4. **Migration Infrastructure**: Migration scripts follow established patterns

### ⚠️ Needs Verification
1. **Instruction Extraction**: Verify that `ell_support` strategies actually contain `implementation` field in production data
2. **Duration Default**: Verify that steps with `duration_minutes = 0` are being caught and fixed
3. **Phase Plan Steps**: Verify that regular phase_plan steps (not vocab/frames) also get proper durations

## Implementation Readiness by Phase

### Phase 1: Backend Data Fixes
**Status**: 🟡 PARTIALLY READY

**What's Done:**
- Duration fix for vocab/frames steps (5 minutes)
- Instruction extraction logic exists

**What Needs Work:**
- [ ] Verify `ell_support` structure in actual lesson JSON
- [ ] Test that instruction extraction works with real data
- [ ] Ensure ALL steps (including phase_plan steps) have non-zero durations
- [ ] Test regeneration of steps to verify fixes

**Risk Level**: 🟢 LOW (no schema changes, can test independently)

### Phase 2: Preview/Live Mode Toggle
**Status**: 🟢 READY

**What's Ready:**
- `useLessonTimer` hook exists and is well-structured
- Schedule entry data structure is known
- Time calculation logic exists

**What Needs Work:**
- [ ] Add `isLiveMode` parameter to hook
- [ ] Modify sync logic conditionally
- [ ] Add UI toggle component
- [ ] Test time window calculation (30 mins before/after)

**Risk Level**: 🟢 LOW (frontend-only, no database changes)

### Phase 3: Database Schema Changes (Structured Fields)
**Status**: 🟡 NEEDS PREPARATION

**What's Ready:**
- Current schema understood
- Migration pattern established
- Both SQLite and Supabase support exists

**What Needs Work:**
- [ ] Create migration script for new structured fields
- [ ] Test migration on sample data
- [ ] Create parsing function for `display_content` → structured fields
- [ ] Update `generate_lesson_steps` to populate both formats
- [ ] Test backward compatibility

**Risk Level**: 🟡 MEDIUM (requires careful migration, data transformation)

### Phase 4: UI Components
**Status**: 🟢 READY

**What's Ready:**
- Component structure understood
- TypeScript interfaces defined
- UI library components available

**What Needs Work:**
- [ ] Create new layout components (TimelineSidebar, etc.)
- [ ] Update LessonMode to use new layout
- [ ] Create resource display components
- [ ] Test responsive design

**Risk Level**: 🟢 LOW (can be done incrementally)

## Critical Prerequisites

### Before Starting Any Phase:
1. **Database Backup**: ✅ Need to confirm backup procedure
2. **Test Environment**: ✅ Need separate test database
3. **Sample Data**: ✅ Need lesson with vocab/frames for testing

### Before Phase 3 (Schema Changes):
1. **Migration Script**: ⚠️ Must be created and tested
2. **Backup Verification**: ⚠️ Must test backup restoration
3. **Rollback Plan**: ⚠️ Must document rollback procedure
4. **Data Validation**: ⚠️ Must validate all existing data can be migrated

## Recommended Implementation Order

### Step 1: Verify Current Implementation (30 min)
- [ ] Check if Phase 1 fixes are already working
- [ ] Test with real lesson data
- [ ] Verify instruction extraction works
- [ ] Document any gaps

### Step 2: Complete Phase 1 (if needed) (1-2 hours)
- [ ] Fix any remaining duration issues
- [ ] Ensure instruction extraction is robust
- [ ] Test regeneration of steps
- [ ] Verify in UI

### Step 3: Implement Phase 2 (2-3 hours)
- [ ] Add Preview/Live mode toggle
- [ ] Update timer hook
- [ ] Add UI controls
- [ ] Test time calculations

### Step 4: Prepare Phase 3 (3-4 hours)
- [ ] Create migration script
- [ ] Test on sample data
- [ ] Create parsing function
- [ ] Test backward compatibility
- [ ] Document rollback procedure

### Step 5: Execute Phase 3 (2-3 hours)
- [ ] Run migration on test database
- [ ] Verify data integrity
- [ ] Update generation code
- [ ] Test with new and old data

### Step 6: Implement Phase 4 (4-6 hours)
- [ ] Create new UI components
- [ ] Update layout
- [ ] Test responsive design
- [ ] Polish UI/UX

## Risk Mitigation Checklist

### Data Safety
- [ ] Database backup created and verified
- [ ] Backup restoration tested
- [ ] Migration script tested on copy of production data
- [ ] Rollback procedure documented and tested

### Testing
- [ ] Unit tests for parsing functions
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for UI components
- [ ] Test with mixed data (old and new formats)

### Monitoring
- [ ] Error logging in place
- [ ] Migration progress tracking
- [ ] Data quality metrics
- [ ] Performance monitoring

## Questions to Resolve

1. **Data Verification**: Do we have access to real lesson JSON to verify `ell_support` structure?
2. **Testing Strategy**: Should we test on production data copy or create synthetic test data?
3. **Deployment**: Should changes be behind feature flags or direct deployment?
4. **Timeline**: What's the target completion date?
5. **Priority**: Which phase provides most immediate value? (Recommend: Phase 1 → Phase 2)

## Ready to Proceed When

- [x] Code structure understood
- [x] Database schema known
- [ ] Sample test data available
- [ ] Migration scripts reviewed
- [ ] Backup procedure confirmed
- [ ] User confirms starting point

## Next Steps

1. **Immediate**: Verify current Phase 1 implementation status
2. **Short-term**: Complete any Phase 1 gaps
3. **Medium-term**: Implement Phase 2 (Preview/Live mode)
4. **Long-term**: Phase 3 and 4 (schema changes and UI)


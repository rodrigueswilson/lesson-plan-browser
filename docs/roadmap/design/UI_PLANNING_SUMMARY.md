# UI Planning Summary: Quick Reference

## MVP Strategy

**v1.0 (MVP) - Initial Release**
- ✅ **Browser Module** (Full implementation) - Priority #1
- ✅ **Simplified Lesson Mode** (Manual navigation, basic timer)

> **Reality check (Nov 2025):**  
> - The Tauri app contains an early Lesson Plan Browser (week/day/lesson views) and a minimal Lesson Mode screen (see `LessonPlanBrowser`, `LessonDetailView`, `LessonMode`).  
> - None of the advanced navigation, filtering, timer synchronization, or Android/React Native parity described below have shipped. Treat unchecked items as **planned** work.

**v2.0 (Future) - Advanced Features**
- ✅ **Advanced Lesson Mode** (Auto-sync, timer adjustment, auto-advance)

## Key Features Planned

### 1. Browser Module (v1 Priority) ✅
- **Current Lesson Display**: Time-based detection, quick actions
- **Schedule Navigation**: Weekly view, day view, slot detail
- **Filtering System**: By subject, date, user, grade
- **Lesson Plan Browser**: List view, detail view, print/export

### 2. Simplified Lesson Mode (v1 MVP) ✅
- **Manual Step Navigation**: Click "Next Step" when ready
- **Step Content Display**: Objectives, sentence frames, materials
- **Basic Timer**: Manual start/stop, countdown only
- **Context-Aware Display**: 
  - Objectives (when needed)
  - Sentence frames (large text, bilingual)
  - Materials list
  - Instruction steps
- **Visual Timer**: Progress bar (green→yellow→red) + countdown

### 3. Advanced Lesson Mode (v2 - Deferred) ⏸️
- **Automatic Timer Synchronization**: Auto-sync with actual time
- **Timer Adjustment**: Reprogram at any step (add/subtract time, skip)
- **Auto-Advance**: Automatically move to next step when timer expires
- **Step Recalculation**: Proportional adjustment of remaining steps

## Platform Support

| Feature | Windows 11 (Tauri) | Android 16 (RN/Capacitor) |
|---------|-------------------|---------------------------|
| Browser Module | ✅ Full support | ✅ Full support |
| Lesson Mode | ✅ Full support | ✅ Full support |
| Timer Sync | ✅ System time | ✅ System time |
| Timer Adjustment | ✅ Modal dialog | ✅ Bottom sheet |
| Context Display | ✅ Side-by-side | ✅ Stacked/Adaptive |

## Data Model Addition

**New Table**: `lesson_steps`
- Stores timed steps for each lesson slot
- Generated from `TailoredInstruction.phase_plan`
- Not printed in DOCX (database only)
- Supports timer adjustment and recalculation

## Recommended Tools

1. **MockFlow** - Sitemap and wireframing
2. **UX Pilot AI** - User journey flows
3. **Google AI Studio** - Data model design

## Implementation Timeline

### v1 MVP (Weeks 1-7)
- **Phase 1-2**: Browser Module Core + Polish (Weeks 1-3) ✅ Priority
- **Phase 3**: Simplified Lesson Mode (Weeks 3-4) ✅ MVP
- **Phase 4-5**: Android Port (Weeks 4-6) ✅ MVP
- **Phase 6**: v1 Release & User Validation (Week 6-7) ✅ Decision Point

### v2 Advanced (Future - Conditional)
- **Phase 7-8**: Advanced Lesson Mode (Only if user validation confirms need)

## Critical Design Decisions

1. **MVP First Approach**:
   - Browser Module: Full implementation (v1)
   - Lesson Mode: Simplified version (v1 MVP)
   - Advanced features: Deferred to v2 (after user validation)

2. **Timer Color Scheme**:
   - Green: 70-100% remaining
   - Yellow: 30-70% remaining
   - Red: <30% remaining

3. **Content Display Priority**:
   - Sentence frames: 48pt+ text (highest priority)
   - Objectives: 36pt+ text
   - Materials: 18pt text
   - Other content: Hidden when not needed

4. **v1 Timer Strategy** (Simplified):
   - Manual start/stop only
   - No automatic synchronization
   - Manual step navigation
   - Timer resets when moving to next step

5. **v2 Timer Strategy** (Future):
   - Automatic time synchronization
   - Timer adjustment/reprogramming
   - Proportional recalculation of remaining steps
   - Auto-advance between steps

## Next Actions

### Immediate (v1 MVP)
1. ✅ Review `UI_PLANNING_DOCUMENT.md` for full specifications
2. ✅ **Prioritize Browser Module** - Begin Phase 1 implementation
3. Set up MockFlow for Browser Module sitemap
4. Begin Phase 1: Browser Module core features

### After v1 Release
1. Gather user feedback on Lesson Mode usage
2. Validate if advanced timer features are needed
3. Decide whether to proceed with v2 enhancements


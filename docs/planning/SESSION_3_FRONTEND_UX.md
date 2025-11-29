# Session 3: Frontend UX Improvements

**Date**: 2025-10-18  
**Status**: READY TO START  
**Estimated Time**: 3-4 hours  
**Risk Level**: LOW (UI changes only)

---

## 📋 Session Overview

Enhance the frontend user experience with better controls, feedback, and progress visibility.

### Features to Implement:
1. **Slot-level reprocessing checkboxes** - Select which slots to reprocess
2. **Source folder path confirmation** - Verify folder before processing
3. **Processing button states** - Show Done/Error states clearly
4. **Progress bar real-time updates** - Fix SSE for live progress

---

## 🎯 Feature 1: Slot-Level Reprocessing Checkboxes

### Current State:
- All slots are processed every time
- No way to selectively reprocess specific slots
- User mentioned: "the slots don't have the checkbox"

### Target State:
- Each slot has a checkbox
- User can select which slots to reprocess
- "Select All" / "Deselect All" buttons
- Only selected slots are sent to backend

### Implementation:

**File**: `frontend/src/components/SlotManager.tsx`

**Changes**:
1. Add state for selected slots:
   ```typescript
   const [selectedSlots, setSelectedSlots] = useState<Set<string>>(new Set());
   ```

2. Add checkbox to each slot:
   ```typescript
   <input
     type="checkbox"
     checked={selectedSlots.has(slot.id)}
     onChange={(e) => toggleSlot(slot.id, e.target.checked)}
   />
   ```

3. Add Select All/None buttons:
   ```typescript
   <Button onClick={selectAll}>Select All</Button>
   <Button onClick={selectNone}>Deselect All</Button>
   ```

4. Filter slots before processing:
   ```typescript
   const slotsToProcess = slots.filter(s => selectedSlots.has(s.id));
   ```

**Estimated Time**: 45 minutes

---

## 🎯 Feature 2: Source Folder Path Confirmation

### Current State:
- User sets base path in settings
- No confirmation before processing
- Errors only appear after processing starts

### Target State:
- Show confirmation dialog before processing
- Display folder path clearly
- Option to change path or proceed
- Verify folder exists

### Implementation:

**File**: `frontend/src/components/WeekProcessor.tsx`

**Changes**:
1. Add confirmation dialog component:
   ```typescript
   const [showConfirmation, setShowConfirmation] = useState(false);
   ```

2. Show dialog before processing:
   ```typescript
   <Dialog open={showConfirmation}>
     <DialogTitle>Confirm Processing</DialogTitle>
     <DialogContent>
       <p>Source folder: {currentUser.base_path_override}</p>
       <p>Week: {weekOf}</p>
       <p>Slots to process: {selectedSlots.size}</p>
     </DialogContent>
     <DialogActions>
       <Button onClick={handleConfirm}>Proceed</Button>
       <Button onClick={handleCancel}>Cancel</Button>
     </DialogActions>
   </Dialog>
   ```

3. Add folder verification:
   ```typescript
   // Check if folder exists via Tauri
   import { exists } from '@tauri-apps/api/fs';
   const folderExists = await exists(basePath);
   ```

**Estimated Time**: 30 minutes

---

## 🎯 Feature 3: Processing Button States

### Current State:
- Button shows "Process Week"
- No visual feedback for completion
- No clear error indication

### Target State:
- **Idle**: "Process Week" (blue)
- **Processing**: "Processing..." (disabled, spinner)
- **Success**: "Done!" (green, checkmark)
- **Error**: "Failed" (red, X icon)
- Auto-reset after 3 seconds

### Implementation:

**File**: `frontend/src/components/WeekProcessor.tsx`

**Changes**:
1. Add button state:
   ```typescript
   type ButtonState = 'idle' | 'processing' | 'success' | 'error';
   const [buttonState, setButtonState] = useState<ButtonState>('idle');
   ```

2. Update button appearance:
   ```typescript
   const buttonConfig = {
     idle: { text: 'Process Week', color: 'primary', icon: null },
     processing: { text: 'Processing...', color: 'primary', icon: <Spinner /> },
     success: { text: 'Done!', color: 'success', icon: <Check /> },
     error: { text: 'Failed', color: 'error', icon: <X /> }
   };
   ```

3. Auto-reset after completion:
   ```typescript
   useEffect(() => {
     if (buttonState === 'success' || buttonState === 'error') {
       const timer = setTimeout(() => setButtonState('idle'), 3000);
       return () => clearTimeout(timer);
     }
   }, [buttonState]);
   ```

**Estimated Time**: 30 minutes

---

## 🎯 Feature 4: Real-Time Progress Updates

### Current State:
- Progress bar exists but may not update in real-time
- SSE (Server-Sent Events) might not be working properly
- User doesn't see live progress

### Target State:
- Progress bar updates as each slot is processed
- Shows current slot being processed
- Displays estimated time remaining
- Works reliably with SSE

### Implementation:

**File**: `frontend/src/lib/api.ts` and `WeekProcessor.tsx`

**Changes**:

1. Fix SSE implementation for Tauri:
   ```typescript
   // Note: Tauri doesn't support EventSource directly
   // Need to use polling or WebSocket alternative
   
   // Option A: Polling
   const pollProgress = async (planId: string) => {
     const interval = setInterval(async () => {
       const progress = await api.get(`/progress/${planId}`);
       onProgress(progress.data);
       if (progress.data.status === 'complete') {
         clearInterval(interval);
       }
     }, 500);
   };
   
   // Option B: Add WebSocket support to backend
   ```

2. Update progress display:
   ```typescript
   <ProgressBar value={progress.percentage} />
   <p>Processing slot {progress.currentSlot} of {progress.totalSlots}</p>
   <p>Current: {progress.currentSubject}</p>
   <p>Estimated time: {progress.estimatedTimeRemaining}s</p>
   ```

3. Add progress state:
   ```typescript
   interface ProgressState {
     percentage: number;
     currentSlot: number;
     totalSlots: number;
     currentSubject: string;
     status: 'idle' | 'processing' | 'complete' | 'error';
   }
   ```

**Estimated Time**: 60 minutes (SSE/polling complexity)

---

## 📊 Implementation Order

### Phase 1: Quick Wins (1.5 hours)
1. ✅ Slot checkboxes (45 min)
2. ✅ Button states (30 min)
3. ✅ Folder confirmation (30 min)

### Phase 2: Complex Feature (1.5 hours)
4. ✅ Real-time progress (60 min)
5. ✅ Testing and polish (30 min)

---

## 🧪 Testing Plan

### Test 1: Slot Selection
- [ ] Check/uncheck individual slots
- [ ] Select All button works
- [ ] Deselect All button works
- [ ] Only selected slots are processed
- [ ] Selection persists during session

### Test 2: Folder Confirmation
- [ ] Dialog appears before processing
- [ ] Shows correct folder path
- [ ] Cancel stops processing
- [ ] Proceed continues processing
- [ ] Invalid folder shows error

### Test 3: Button States
- [ ] Button shows "Processing..." during work
- [ ] Button shows "Done!" on success
- [ ] Button shows "Failed" on error
- [ ] Auto-resets after 3 seconds
- [ ] Disabled during processing

### Test 4: Progress Updates
- [ ] Progress bar moves smoothly
- [ ] Current slot displayed
- [ ] Subject name shown
- [ ] Updates in real-time
- [ ] Completes at 100%

---

## 📁 Files to Modify

1. **frontend/src/components/SlotManager.tsx** - Add checkboxes
2. **frontend/src/components/WeekProcessor.tsx** - Button states, confirmation
3. **frontend/src/lib/api.ts** - Progress polling
4. **frontend/src/store/useStore.ts** - Add selectedSlots state

---

## 🎨 UI Components Needed

### New Components:
1. **ConfirmationDialog** - Folder path confirmation
2. **ProgressDisplay** - Enhanced progress with details

### Modified Components:
1. **SlotCard** - Add checkbox
2. **ProcessButton** - State-based styling
3. **ProgressBar** - Real-time updates

---

## 🔧 Technical Decisions

### Decision 1: Progress Updates
**Options**:
- A) SSE (Server-Sent Events) - Standard but Tauri doesn't support
- B) Polling - Simple, works everywhere
- C) WebSocket - Complex, requires backend changes

**Choice**: **Polling** (Option B)
- Simple to implement
- Works reliably in Tauri
- 500ms interval is responsive enough
- No backend changes needed

### Decision 2: Slot Selection Storage
**Options**:
- A) Component state - Lost on unmount
- B) Zustand store - Persists during session
- C) LocalStorage - Persists across sessions

**Choice**: **Zustand store** (Option B)
- Persists during session
- Easy to access from multiple components
- No need for cross-session persistence

### Decision 3: Button State Reset
**Options**:
- A) Manual reset - User clicks to reset
- B) Auto-reset - Resets after delay
- C) Next action reset - Resets on next interaction

**Choice**: **Auto-reset** (Option B)
- Better UX - no extra click needed
- 3 second delay is enough to see result
- Keeps UI clean

---

## 📈 Success Criteria

### Must Have:
- ✅ Slot checkboxes functional
- ✅ Select All/None works
- ✅ Only selected slots processed
- ✅ Button shows processing state
- ✅ Button shows success/error
- ✅ Confirmation dialog appears

### Nice to Have:
- ✅ Progress updates in real-time
- ✅ Estimated time remaining
- ✅ Current slot displayed
- ✅ Smooth animations

---

## 🚀 Getting Started

### Prerequisites:
- ✅ Session 2 complete
- ✅ Frontend working
- ✅ Backend running
- ✅ Database clean

### First Steps:
1. Create feature branch (optional)
2. Start with slot checkboxes (easiest)
3. Test each feature before moving to next
4. Keep frontend running for live testing

---

## 📝 Notes

- All changes are frontend-only (low risk)
- No database changes needed
- No backend API changes needed
- Can implement incrementally
- Each feature is independent

---

**Ready to start? Let's begin with Feature 1: Slot Checkboxes!** 🚀

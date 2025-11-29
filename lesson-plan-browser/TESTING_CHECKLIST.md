# Testing Checklist - Lesson Plan Browser

## Phase 6: PC Version Testing

### Prerequisites
- [ ] Backend is running on `http://localhost:8000`
- [ ] Database has test data (users, lesson plans, schedules)
- [ ] JSON lesson plan files exist in user's base path

### Setup
```bash
cd lesson-plan-browser/frontend
npm install
npm run tauri:dev
```

---

## 6.1 Browser Functionality Tests

### Week Selection
- [ ] Week selector displays available weeks
- [ ] Weeks from database appear in selector
- [ ] Weeks from JSON files appear in selector
- [ ] Can select different weeks

### Week View
- [ ] Week view loads correctly
- [ ] Lessons display in correct time slots
- [ ] Subject colors display correctly
- [ ] Non-class periods (Lunch, Prep, etc.) display correctly
- [ ] Can click on lessons to view details

### Day View
- [ ] Can switch to day view
- [ ] Day view shows lessons for selected day
- [ ] Can navigate between days (previous/next)
- [ ] Lessons display with correct subject, grade, homeroom
- [ ] Can click lessons to view details

### Lesson Detail View
- [ ] Lesson detail view opens when clicking a lesson
- [ ] Displays lesson plan content correctly
- [ ] Shows WIDA objectives
- [ ] Shows vocabulary and cognates
- [ ] Shows sentence frames
- [ ] Shows materials needed
- [ ] "Enter Lesson Mode" button is visible and functional
- [ ] Can navigate back to browser

### Data Sources
- [ ] Can read lesson plans from database
- [ ] Can read lesson plans from JSON files
- [ ] Both sources appear in week selector
- [ ] Refresh button clears cache and reloads data

---

## 6.2 Lesson Mode Functionality Tests

### Entry into Lesson Mode
- [ ] Can enter Lesson Mode from Lesson Detail View
- [ ] Lesson Mode opens with correct lesson
- [ ] Schedule entry passed correctly

### Step Navigation
- [ ] Timeline sidebar displays all steps
- [ ] Can navigate to previous step
- [ ] Can navigate to next step
- [ ] Current step is highlighted in timeline
- [ ] Step content displays correctly

### Timer Functionality
- [ ] Timer displays current step duration
- [ ] Timer starts when step begins
- [ ] Timer counts down correctly
- [ ] Timer shows remaining time
- [ ] Can pause timer
- [ ] Can resume timer
- [ ] Can adjust step durations
- [ ] Timer adjustments persist

### Session Management
- [ ] Session state saves correctly
- [ ] Session state restores on app restart
- [ ] Current step index persists
- [ ] Timer state persists
- [ ] Adjusted durations persist

### Resource Display
- [ ] Resources display correctly
- [ ] Vocabulary displays with highlighting
- [ ] Sentence frames display correctly
- [ ] Materials list displays correctly

### Exit Lesson Mode
- [ ] Can exit Lesson Mode
- [ ] Returns to browser view
- [ ] Browser maintains previous state

---

## 6.3 Integration Tests

### Navigation Flow
- [ ] Browser → Lesson Detail → Lesson Mode → Browser
- [ ] Navigation works smoothly
- [ ] No errors in console

### Data Loading
- [ ] Plan data loads correctly from both sources
- [ ] No duplicate plans shown
- [ ] Cache works correctly (30 second duration)
- [ ] Refresh button works

### Performance
- [ ] No noticeable lag when navigating
- [ ] Fast response to clicks
- [ ] Smooth transitions between views

---

## Known Issues / Notes

### Expected Behaviors
- PC version connects to backend at `http://localhost:8000`
- Uses HTTP API for all data access
- Standalone mode (local database) will be enabled in Phase 9 (Android)

### Common Issues
- **Backend not running**: App will fail to load users/plans
- **No data**: Week selector may be empty if no plans exist
- **Import errors**: May need to install dependencies (`npm install`)

---

## Next Steps After Testing

Once PC version is working:
1. Phase 7: Configure Android build
2. Phase 8: Optimize bundle size
3. Phase 9: Implement standalone architecture (local database + sync)


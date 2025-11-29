# MockFlow AI Wireframe Generation Prompts
## Optimized Prompts Based on UI Planning Document

**Purpose**: Consistent, detailed prompts for MockFlow's "Generate Wireframe with AI" feature  
**AI Credits**: ~15-20 credits per wireframe (use wisely)  
**Strategy**: Use detailed prompts to get better initial results, then refine manually

---

## Prompt Structure Best Practices

### Effective Prompt Formula:
```
[Screen Type] for [Feature] - [Platform]
[Key Components List]
[Layout Description]
[Specific Requirements]
[Context/Use Case]
```

### What Makes a Good Prompt:
1. ✅ **Specific screen type** (Dashboard, Detail View, etc.)
2. ✅ **Component list** (what needs to be on screen)
3. ✅ **Layout description** (where things go)
4. ✅ **Platform context** (Desktop/Windows or Mobile/Android)
5. ✅ **User context** (who uses it and why)

### What to Avoid:
- ❌ Vague descriptions ("a nice UI")
- ❌ Too many screens in one prompt
- ❌ Design details (colors, fonts - not needed for wireframes)
- ❌ Overly complex requirements (keep it focused)

---

## Prompt 1: 
```

**Estimated Credits**: 15-20 credits  
**Refinement Needed**: Manual adjustments for exact spacing, component details

---

## Prompt 2: Browser Module - Schedule View & Filtering

### Desktop/Windows Version:

```
Create a wireframe for a desktop schedule management screen for Windows 11.

Screen: Schedule View with Filtering

Key Components:
- Header: Navigation breadcrumbs and title
- Filter Panel (left sidebar or top bar):
  * Filter by Subject (dropdown)
  * Filter by Date Range (date picker)
  * Filter by Grade (dropdown)
  * Filter by User/Teacher (dropdown)
  * "Apply Filters" and "Clear Filters" buttons
- Schedule Display Area (main content):
  * Weekly Calendar View (grid layout):
    - Days of week as columns (Mon-Fri)
    - Time slots as rows
    - Lesson blocks in cells
  * OR List View (alternative):
    - List of lessons with subject, time, grade
    - Clickable to view details
- Lesson Detail Panel (right sidebar, when lesson selected):
  * Lesson plan preview
  * Quick actions (View Full Plan, Enter Lesson Mode)

Layout Requirements:
- Filters should be easily accessible but not intrusive
- Schedule display should be the main focus
- Multiple view options (calendar/list) should be toggleable
- Detail panel should slide in when lesson is selected
- Desktop-optimized layout (not mobile)

User Context: Teachers need to browse and filter their weekly schedule efficiently. Should support both calendar and list views.
```

**Estimated Credits**: 15-20 credits  
**Refinement Needed**: Manual adjustments for filter panel placement, calendar grid details

---

## Prompt 3: Lesson Mode - Active Lesson View (MVP)

### Desktop/Windows Version:

```
Create a wireframe for a desktop lesson mode screen for Windows 11.

Screen: Active Lesson View (Simplified MVP - Manual Navigation)

Key Components:
- Header: Lesson info (Subject, Grade, Step X of Y)
- Timer Display Section (top, prominent):
  * Visual progress bar (horizontal, color-coded: green/yellow/red)
  * Countdown timer (large text, e.g., "8:32 remaining")
  * Control buttons: "Start Timer", "Stop Timer", "Reset" (manual control only)
- Current Step Content Area (main, large):
  * Step name (e.g., "Practice - Step 3 of 5")
  * Content display area (context-aware):
    - For sentence frames: Large text boxes (48pt+), Portuguese on top, English below
    - For objectives: Centered text boxes with objective content
    - For materials: Bulleted list
  * Content should be large and readable (for classroom display)
- Step Navigation (bottom):
  * Progress indicators: [1✓] [2✓] [3●] [4○] [5○]
  * "Previous Step" and "Next Step" buttons (manual navigation)
- Footer: "Exit Lesson Mode" button

Layout Requirements:
- Timer should be visible but not overwhelming
- Step content should be the main focus (large, centered)
- Navigation should be clear but not distracting
- Full-screen or near-full-screen layout (for classroom projection)
- Desktop-optimized (not mobile)

User Context: Teachers use this during active lessons. Content needs to be large enough for students to see. Manual step navigation (no auto-advance in MVP).
```

**Estimated Credits**: 15-20 credits  
**Refinement Needed**: Manual adjustments for exact text sizes, content area layout variations

---

## Prompt 4: Lesson Mode - Mobile/Android Version

### Mobile/Android Version:

```
Create a wireframe for a mobile lesson mode screen for Android tablet/phone.

Screen: Active Lesson View (Mobile - Portrait Orientation)

Key Components:
- Compact Header: Lesson info (Subject, Step X of Y)
- Timer Display (top section):
  * Circular or horizontal progress bar
  * Countdown timer (large, readable)
  * "Start/Stop" button (compact)
- Step Content Area (main, scrollable):
  * Step name
  * Content display:
    - Sentence frames: Stacked vertically, Portuguese then English (large text)
    - Objectives: Full-width text boxes
    - Materials: Scrollable list
- Step Navigation (bottom, fixed):
  * Horizontal progress dots: [●] [●] [●] [○] [○]
  * "Previous" and "Next" buttons
- Bottom Navigation Bar: "Exit Lesson Mode"

Layout Requirements:
- Mobile-first design (portrait orientation)
- Touch-friendly buttons (large tap targets)
- Scrollable content area (for longer content)
- Bottom navigation should be easily accessible
- Optimized for tablet (larger screen) but works on phone

User Context: Teachers use Android tablets during lessons. Needs to be touch-friendly and readable in classroom setting.
```

**Estimated Credits**: 15-20 credits  
**Refinement Needed**: Manual adjustments for exact mobile spacing, touch target sizes

---

## Prompt 5: SiteMap/Navigation Structure

### For SiteMap Project:

```
Create a sitemap for a bilingual lesson plan application.

Application Structure:
- Root: App Entry Point
- Browser Module:
  * Dashboard (Current Lesson)
  * Schedule View (Weekly Calendar)
  * Lesson Plan Browser (List View)
  * Lesson Plan Detail View
  * Filtering System
- Lesson Mode:
  * Entry Screen (Select Lesson)
  * Active Lesson View (Step-by-Step)
  * Step Navigation

Navigation Flow:
- Dashboard → Schedule View → Lesson Detail → Enter Lesson Mode
- Dashboard → Lesson Plan Browser → Lesson Detail
- Lesson Mode → Exit → Back to Dashboard
- All screens accessible via main navigation

User Types:
- Primary: Teachers (main users)
- Secondary: Administrators (future)

Key Transitions:
- Browser Module ↔ Lesson Mode (bidirectional)
- Schedule View ↔ Lesson Detail (bidirectional)
- Lesson Plan Browser ↔ Lesson Detail (bidirectional)
```

**Estimated Credits**: 5-10 credits (SiteMap uses fewer credits)  
**Refinement Needed**: Manual adjustments for exact navigation paths

---

## Advanced: Combined Prompt Strategy

### If You Want to Combine Screens (Save Credits):

**Prompt for Combined Browser Module Page:**

```
Create a wireframe showing two related screens for a desktop lesson plan browser:

Screen 1 (Left Side): Current Lesson Dashboard
- Header with app title
- Current lesson card (prominent)
- Time remaining countdown
- Action buttons
- Week overview

Screen 2 (Right Side): Schedule View
- Filter panel (top)
- Weekly calendar grid
- Lesson detail panel (when selected)

Show both screens side-by-side to demonstrate the relationship between dashboard and schedule view. Use annotations to show navigation flow between screens.
```

**Estimated Credits**: 20-25 credits (more complex, but gets both screens)  
**Trade-off**: Less detail per screen, but saves one page slot

---

## Prompt Refinement Tips

### After Initial Generation:

1. **Review the Output**
   - Does it match your requirements?
   - Are components in the right places?
   - Is the layout logical?

2. **Manual Refinements** (No Credits Needed)
   - Adjust component sizes
   - Move elements around
   - Add/remove components
   - Use MockFlow's UI packs for specific components

3. **Iterate with Smaller Prompts** (If Needed)
   - Use 2-5 credits for specific component adjustments
   - Example: "Add a filter dropdown to the top right"
   - Example: "Make the timer display larger and more prominent"

### When to Use More Credits:
- ✅ Initial wireframe generation (worth it)
- ✅ Major layout changes (if manual editing is difficult)
- ❌ Minor adjustments (do manually)
- ❌ Color/styling details (not needed for wireframes)

---

## Credit Usage Strategy

### Recommended Allocation:

**Total: 100 Credits**

1. **Page 1 (Browser Module)**: 20 credits
   - Initial generation: 15 credits
   - Refinements: 5 credits

2. **Page 2 (Lesson Mode)**: 20 credits
   - Initial generation: 15 credits
   - Refinements: 5 credits

3. **Page 3 (Navigation/SiteMap)**: 10 credits
   - SiteMap generation: 5 credits
   - Navigation flow: 5 credits

4. **Reserve**: 50 credits
   - For unexpected needs
   - For component-specific generations
   - For alternative layouts

### Alternative Strategy (More Conservative):

1. **Page 1**: 15 credits (initial only, refine manually)
2. **Page 2**: 15 credits (initial only, refine manually)
3. **Page 3**: 10 credits (SiteMap)
4. **Reserve**: 60 credits (for future needs)

---

## Prompt Templates for Quick Use

### Template 1: Dashboard Screen

```
Create a wireframe for a [platform] [feature] dashboard.

Key Components:
- [Component 1]: [Description]
- [Component 2]: [Description]
- [Component 3]: [Description]

Layout: [Brief layout description]

User Context: [Who uses it and why]
```

### Template 2: Detail View Screen

```
Create a wireframe for a [platform] [feature] detail view.

Key Components:
- Header: [Description]
- Main Content: [Description]
- Sidebar/Panel: [Description]
- Actions: [Description]

Layout: [Brief layout description]

User Context: [Who uses it and why]
```

### Template 3: Form/Input Screen

```
Create a wireframe for a [platform] [feature] form screen.

Key Components:
- Form Fields: [List fields]
- Validation: [How errors are shown]
- Actions: [Submit/Cancel buttons]
- Help Text: [Where help appears]

Layout: [Brief layout description]

User Context: [Who uses it and why]
```

---

## Best Practices Summary

### ✅ DO:
- Use detailed, specific prompts
- Include component lists
- Specify platform (Desktop/Mobile)
- Mention user context
- Start with our pre-written prompts
- Refine manually after generation
- Export/screenshot early versions

### ❌ DON'T:
- Use vague descriptions
- Try to generate multiple unrelated screens in one prompt
- Worry about colors/styling (wireframes are low-fidelity)
- Use credits for minor adjustments
- Generate the same screen multiple times

---

## Next Steps

1. ✅ **Start with Prompt 1** (Browser Module Dashboard)
   - Copy the prompt exactly
   - Generate wireframe
   - Review and refine manually
   - Export/screenshot and share with me

2. ✅ **Then Prompt 2** (Schedule View)
   - Or combine with Prompt 1 if you want to save pages

3. ✅ **Then Prompt 3** (Lesson Mode)
   - Generate desktop version first
   - Then mobile version if needed

4. ✅ **Share Results**
   - Screenshots + descriptions
   - I'll provide feedback and refinement suggestions

---

## Questions to Consider

Before generating, ask yourself:

1. **Which screen is highest priority?**
   - Start with Browser Module Dashboard (Prompt 1)

2. **Do I want separate mobile wireframes?**
   - Desktop first, mobile can be adapted later
   - Or generate both if you have credits

3. **Should I combine screens?**
   - Can save page slots but uses more credits
   - Better to have separate pages for clarity

4. **How detailed should I be?**
   - More detail = better initial result
   - But don't overthink - wireframes are meant to be refined

---

**Ready to start?** Use Prompt 1 for Browser Module Dashboard, then share the results!


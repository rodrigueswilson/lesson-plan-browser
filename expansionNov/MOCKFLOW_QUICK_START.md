# MockFlow Quick Start Guide
## How to Use the AI Prompts

**Important**: Use **ONE prompt at a time** - each prompt generates one wireframe.

---

## Step-by-Step Instructions

### Step 1: Choose Your Prompt

From `MOCKFLOW_AI_PROMPTS.md`, select ONE prompt:
- **Prompt 1**: Browser Module Dashboard (start here)
- **Prompt 2**: Schedule View & Filtering
- **Prompt 3**: Lesson Mode Active View
- **Prompt 4**: Lesson Mode Mobile
- **Prompt 5**: SiteMap/Navigation

### Step 2: Copy ONLY the Prompt Text

**What to Copy:**
- ✅ Copy ONLY the text between the triple backticks (```)
- ✅ Include the entire prompt text
- ✅ Don't copy the markdown formatting

**Example - Prompt 1:**

```
✅ COPY THIS PART (everything between the backticks):

Create a wireframe for a desktop lesson plan browser dashboard for Windows 11.

Screen: Current Lesson Dashboard (Main Screen)

Key Components:
- Header: App title "Bilingual Lesson Planner" with navigation
- Current Lesson Card (prominent, centered):
  * Subject and grade (e.g., "Math - 5th Grade")
  * Time range (e.g., "1:06 PM - 1:47 PM")
  * Time remaining countdown (large, prominent)
  * Two action buttons: "View Full Plan" and "Enter Lesson Mode"
- Previous/Next Lesson Cards (side by side, below current lesson):
  * Left: Previous lesson preview
  * Right: Next lesson preview
- Week Overview (sidebar or bottom section):
  * Calendar showing Mon-Fri
  * Number of lessons per day

Layout Requirements:
- Current lesson card should be the focal point (largest element)
- Time remaining should be visually distinct (large text, colored)
- Action buttons should be easily accessible (primary button style)
- Navigation should be intuitive (clear visual hierarchy)
- Responsive to desktop screen size (not mobile)

User Context: Teachers need quick access to current lesson with time awareness. Should be scannable at a glance.

❌ DON'T COPY:
- The markdown headers (## Prompt 1: ...)
- The "Estimated Credits" line
- The "Refinement Needed" line
- The triple backticks themselves
```

### Step 3: Paste into MockFlow

1. Open MockFlow
2. Create a new Wireframe Project (or open existing)
3. Click "Generate Wireframe with AI" (or similar button)
4. Paste your copied prompt into the text field
5. Click "Generate" or "Create"

### Step 4: Review and Refine

- Review the generated wireframe
- Make manual adjustments (no credits needed)
- Export/screenshot when ready

### Step 5: Repeat for Next Prompt

- Go back to `MOCKFLOW_AI_PROMPTS.md`
- Select the next prompt
- Copy only that prompt's text
- Generate the next wireframe

---

## Visual Guide: What to Copy

### ✅ CORRECT - Copy This:

```
Create a wireframe for a desktop lesson plan browser dashboard for Windows 11.

Screen: Current Lesson Dashboard (Main Screen)

Key Components:
- Header: App title "Bilingual Lesson Planner" with navigation
- Current Lesson Card (prominent, centered):
  * Subject and grade (e.g., "Math - 5th Grade")
  * Time range (e.g., "1:06 PM - 1:47 PM")
  * Time remaining countdown (large, prominent)
  * Two action buttons: "View Full Plan" and "Enter Lesson Mode"
- Previous/Next Lesson Cards (side by side, below current lesson):
  * Left: Previous lesson preview
  * Right: Next lesson preview
- Week Overview (sidebar or bottom section):
  * Calendar showing Mon-Fri
  * Number of lessons per day

Layout Requirements:
- Current lesson card should be the focal point (largest element)
- Time remaining should be visually distinct (large text, colored)
- Action buttons should be easily accessible (primary button style)
- Navigation should be intuitive (clear visual hierarchy)
- Responsive to desktop screen size (not mobile)

User Context: Teachers need quick access to current lesson with time awareness. Should be scannable at a glance.
```

### ❌ WRONG - Don't Copy This:

```
## Prompt 1: Browser Module - Current Lesson Dashboard

### Desktop/Windows Version:

```
Create a wireframe for a desktop lesson plan browser dashboard...
```

**Estimated Credits**: 15-20 credits  
**Refinement Needed**: Manual adjustments...
```

---

## Quick Reference: Copy-Paste Ready Prompts

### Prompt 1: Browser Module Dashboard

```
Create a wireframe for a desktop lesson plan browser dashboard for Windows 11.

Screen: Current Lesson Dashboard (Main Screen)

Key Components:
- Header: App title "Bilingual Lesson Planner" with navigation
- Current Lesson Card (prominent, centered):
  * Subject and grade (e.g., "Math - 5th Grade")
  * Time range (e.g., "1:06 PM - 1:47 PM")
  * Time remaining countdown (large, prominent)
  * Two action buttons: "View Full Plan" and "Enter Lesson Mode"
- Previous/Next Lesson Cards (side by side, below current lesson):
  * Left: Previous lesson preview
  * Right: Next lesson preview
- Week Overview (sidebar or bottom section):
  * Calendar showing Mon-Fri
  * Number of lessons per day

Layout Requirements:
- Current lesson card should be the focal point (largest element)
- Time remaining should be visually distinct (large text, colored)
- Action buttons should be easily accessible (primary button style)
- Navigation should be intuitive (clear visual hierarchy)
- Responsive to desktop screen size (not mobile)

User Context: Teachers need quick access to current lesson with time awareness. Should be scannable at a glance.
```

### Prompt 2: Schedule View

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

### Prompt 3: Lesson Mode Active View

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

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Copying the Entire Document
**Wrong**: Pasting the entire `MOCKFLOW_AI_PROMPTS.md` file
**Right**: Copy only one prompt's text

### ❌ Mistake 2: Including Markdown Formatting
**Wrong**: Including `## Prompt 1:` headers and backticks
**Right**: Copy only the plain text prompt

### ❌ Mistake 3: Copying Multiple Prompts
**Wrong**: Trying to generate multiple wireframes at once
**Right**: Generate one wireframe at a time

### ❌ Mistake 4: Including Metadata
**Wrong**: Including "Estimated Credits" or "Refinement Needed" lines
**Right**: Copy only the prompt description

---

## Workflow Summary

1. **Open** `MOCKFLOW_AI_PROMPTS.md`
2. **Find** the prompt you want (e.g., Prompt 1)
3. **Copy** only the text between the triple backticks (```)
4. **Paste** into MockFlow's AI generation field
5. **Generate** the wireframe
6. **Refine** manually (no credits needed)
7. **Export/Screenshot** and share with me
8. **Repeat** for next prompt

---

## Tips for Best Results

1. **Copy exactly** - Don't modify the prompt text
2. **One at a time** - Generate one wireframe per prompt
3. **Review first** - Check the output before refining
4. **Manual refinement** - Use MockFlow's tools for adjustments (saves credits)
5. **Export early** - Save versions as you go

---

## Need Help?

If MockFlow's AI doesn't understand the prompt:
- Try simplifying (remove some details)
- Break into smaller prompts
- Use MockFlow's manual tools to refine

**Remember**: The prompts are optimized, but AI results may vary. Manual refinement is expected and doesn't cost credits!


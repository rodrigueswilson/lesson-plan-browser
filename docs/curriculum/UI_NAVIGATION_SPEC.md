# Curriculum UI Navigation Specification

## Goal

Make curriculum exploration obvious, fast, and pedagogically useful for teachers.

## Information architecture

### Layout

- Left pane: hierarchy explorer (Grade -> Subject -> Unit).
- Right pane: active content area.
- Top sticky navigation bar in right pane:
  - breadcrumb (`Grade > Subject > Unit > Lesson`)
  - unit selector
  - lesson selector
  - previous/next lesson
  - previous/next unit
  - quick links to related units (previous grade and next grade)

### Content sections

- Tab 1: Unit Overview
- Tab 2: Lessons
- Tab 3: Source and lineage

## Interaction rules

- Clicking a lesson updates active lesson and scrolls content header into view.
- Active lesson title and number must be visible at top immediately.
- Previous/next controls are keyboard and mouse accessible.
- Navigation state persists while browsing within selected unit.

## Required UX improvements from current MVP

- Reduce dependence on distant card grid area for context.
- Keep selected lesson context near top.
- Make lesson-to-lesson progression explicit.
- Add unit-to-unit navigation within same grade/subject.

## Cross-grade semantic linkage (teacher priority)

### User story

As a teacher planning Grade N unit content, I need one-click access to equivalent units in Grade N-1 and N+1 to understand vertical progression.

### UI placement

In top bar and unit summary card:
- related previous grade unit
- related next grade unit
- relation badge (for example `Geometry progression`, `Fractions progression`)

### Behavior

- If multiple related units exist, show a compact list sorted by confidence.
- Each link shows rationale tooltip (manual mapping or semantic suggestion).

## Accessibility and clarity requirements

- High-contrast selected states.
- Focus ring on keyboard navigation.
- Clear empty states (no lessons, no related units, no intro).
- Avoid dense card-only interactions for primary navigation.

## Acceptance criteria

- Teacher reaches any adjacent lesson in one click or less after a lesson is selected.
- Teacher reaches previous/next grade related unit in two clicks or less.
- No loss of visible context when switching lessons.

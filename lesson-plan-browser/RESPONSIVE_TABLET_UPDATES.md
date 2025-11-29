# Responsive Tablet Updates

## Overview

Updated shared components to be optimized for tablet screens with larger touch targets and improved readability.

---

## Changes Made

### 1. TimerDisplay Component (`shared/lesson-mode/src/components/TimerDisplay.tsx`)

#### Timer Display
- **Mobile/Tablet**: `text-6xl` (96px)
- **Desktop**: `text-4xl` (36px)
- **Status text**: Larger `text-base` on mobile, `text-sm` on desktop

#### Progress Bar
- **Mobile/Tablet**: `h-6` (24px height)
- **Desktop**: `h-4` (16px height)

#### Buttons (Start, Pause, Reset, Adjust)
- **Mobile/Tablet**: 
  - Height: `h-12` (48px)
  - Padding: `px-6` (24px horizontal)
  - Text: `text-base` (16px)
  - Icons: `w-5 h-5` (20px)
- **Desktop**:
  - Height: `h-9` (36px)
  - Padding: `px-4` (16px horizontal)
  - Text: `text-sm` (14px)
  - Icons: `w-4 h-4` (16px)

#### Card Padding
- **Mobile/Tablet**: `p-8` (32px)
- **Desktop**: `p-6` (24px)

---

### 2. SentenceFramesDisplay Component (`shared/lesson-mode/src/components/resources/SentenceFramesDisplay.tsx`)

#### Expanded View Text
- **Default font size**: 48px (was dynamic only)
- **Line height**: `1.3` for better readability
- **Bottom margin**: `mb-8` on mobile, `mb-6` on desktop

#### Language Function Badge
- **Mobile/Tablet**:
  - Padding: `px-6 py-3` (24px×12px)
  - Text: `text-lg` (18px)
  - Margin: `mt-8` (32px)
- **Desktop**:
  - Padding: `px-4 py-2` (16px×8px)
  - Text: `text-base` (16px)
  - Margin: `mt-6` (24px)

#### Metadata Text
- **Mobile/Tablet**: `text-xl` (20px), font-medium
- **Desktop**: `text-base` (16px)

#### List View Cards
- **Mobile/Tablet**:
  - Padding: `p-6` (24px)
  - Text: `text-2xl` (24px)
  - Badge padding: `px-3 py-1`
  - Badge text: `text-sm` (14px)
- **Desktop**:
  - Padding: `p-4` (16px)
  - Text: `text-xl` (20px)
  - Badge padding: `px-2 py-0.5`
  - Badge text: `text-xs` (12px)

---

### 3. ExpandableItemView Component (`shared/lesson-mode/src/components/resources/ExpandableItemView.tsx`)

#### Header Bar
- **Padding**: `p-6` on mobile, `p-4` on desktop
- **Close Button**:
  - Height: `h-12` on mobile, `h-9` on desktop
  - Padding: `px-6` on mobile, `px-4` on desktop
  - Text: `text-base` on mobile, `text-sm` on desktop
  - Icon: `w-5 h-5` on mobile, `w-4 h-4` on desktop
- **Counter Text**: `text-lg` on mobile, `text-sm` on desktop

#### Navigation Buttons (Previous/Next)
- **Mobile/Tablet**:
  - Size: `w-16 h-16` (64px×64px)
  - Icons: `w-8 h-8` (32px)
- **Desktop**:
  - Size: `w-12 h-12` (48px×48px)
  - Icons: `w-6 h-6` (24px)

---

## Responsive Strategy

All responsive changes use Tailwind's `md:` breakpoint:
- **Mobile/Tablet** (default): < 768px width
- **Desktop** (`md:`): ≥ 768px width

### Design Principles

1. **Touch Targets**: Minimum 48px height for all interactive elements on mobile
2. **Text Legibility**: Larger text sizes for tablet viewing distances
3. **Spacing**: Increased padding and margins on mobile for better touch ergonomics
4. **Icons**: Larger icons on mobile for better visibility

---

## Testing Checklist

- [ ] Timer buttons are easily tappable on tablet
- [ ] Timer display is clearly readable from normal viewing distance
- [ ] Sentence frames text is legible and properly sized
- [ ] Navigation arrows are large enough for easy tapping
- [ ] All text scales appropriately between mobile and desktop views
- [ ] No text overflow or layout issues on tablet screen

---

## Files Modified

1. `shared/lesson-mode/src/components/TimerDisplay.tsx`
2. `shared/lesson-mode/src/components/resources/SentenceFramesDisplay.tsx`
3. `shared/lesson-mode/src/components/resources/ExpandableItemView.tsx`

---

## Next Steps

1. Build and test on Android emulator
2. Deploy to physical tablet
3. Verify all views work correctly with new sizing
4. Adjust if needed based on real-world usage

---

**Last Updated:** 2025-11-27  
**Status:** Ready for testing


# Objectives DOCX Generation Fixes

## Date
2025-01-27

## Issues Fixed

### Issue 1: Portrait Instead of Landscape Orientation

**Problem:**
The objectives DOCX was being generated in portrait orientation instead of landscape.

**Root Cause:**
In python-docx, setting `section.orientation = WD_ORIENT.LANDSCAPE` alone is not sufficient. You must also explicitly set the page width and height.

**Fix Applied:**
Added explicit page dimension settings:
```python
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width = Inches(11)   # Landscape width
section.page_height = Inches(8.5)  # Landscape height
```

**Location:** `backend/services/objectives_printer.py` lines 590-593

---

### Issue 2: Margins Not Set to 0.5 Inches

**Problem:**
Margins were not consistently set to 0.5 inches.

**Fix Applied:**
Verified and ensured all margins are set to 0.5 inches:
```python
section.top_margin = Inches(0.5)
section.bottom_margin = Inches(0.5)
section.left_margin = Inches(0.5)
section.right_margin = Inches(0.5)
```

**Location:** `backend/services/objectives_printer.py` lines 595-598

---

### Issue 3: Font Size Too Small - Not Filling 3/4 of Page

**Problem:**
Student Goal text was too small and not filling the available 3/4 of the landscape page.

**Root Cause:**
The font size calculation was too conservative and didn't properly account for text wrapping. It was calculating based on single-line width constraints rather than maximizing height fill with wrapping.

**Fix Applied:**

1. **Improved font size calculation algorithm:**
   - For wrapping text, uses formula: `F ≈ sqrt(H * 72² * W / (L * 0.55 * 1.25))`
   - Where: F = font_size, H = height_target, W = available_width, L = total_chars
   - Prioritizes filling 85% of available height
   - Allows text to wrap naturally to fit width

2. **Increased base font size parameters:**
   - Base font size: 48pt → 72pt
   - Min font size: 16pt → 24pt
   - Max font size: 88pt → 120pt

3. **Added paragraph formatting for wrapping:**
   - Enabled word wrapping
   - Set line spacing to 1.25 for proper fill

**Location:** 
- Font calculation: `backend/services/objectives_printer.py` lines 422-479
- Font parameters: `backend/services/objectives_printer.py` lines 659-661
- Paragraph formatting: `backend/services/objectives_printer.py` lines 671-673

---

## Test Results

✅ **All fixes verified:**

- **Landscape Orientation:** ✅ Confirmed (11" × 8.5")
- **Margins:** ✅ All set to 0.5 inches
- **Font Sizing:** ✅ Now fills ~85% of available height (50pt for 120-char text)

**Example Test:**
- Text: 120 characters
- Available space: 9.4" × 5.0" (3/4 of landscape page)
- Calculated font size: 50pt
- Estimated fill: 84.7% of available height

---

## Page Layout

**Landscape US Letter:**
- Page size: 11" × 8.5"
- Margins: 0.5" all sides
- Usable area: 10" × 7.5"

**Content Distribution:**
- Header: ~0.3" (Date | Subject | Grade | Homeroom, 10pt)
- Student Goal: ~5.625" (3/4 of 7.5", large bold text, fills ~85% of this space)
- Separator: Thin gray line
- WIDA Objective: ~1.875" (1/4 of 7.5", smaller gray text)

---

## Code Changes Summary

1. ✅ Fixed landscape orientation (explicit page dimensions)
2. ✅ Verified 0.5" margins
3. ✅ Improved font size calculation to maximize height fill
4. ✅ Increased font size parameters (base/min/max)
5. ✅ Added paragraph formatting for proper wrapping

All changes are in `backend/services/objectives_printer.py`.


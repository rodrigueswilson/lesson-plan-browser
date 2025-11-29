# MockFlow Troubleshooting Guide
## When AI Generates Wrong Content

**Problem**: MockFlow AI generated a website about "creative space for brands" instead of lesson plan browser dashboard.

---

## Why This Happens

MockFlow's AI might:
1. **Misinterpret the prompt** - Not understanding the educational context
2. **Use wrong templates** - Defaulting to marketing/website templates
3. **Need more explicit instructions** - Requiring clearer wireframe specifications
4. **Have different AI modes** - May need to specify "wireframe" vs "website"

---

## Solution 1: More Explicit Wireframe Prompt

Try this **revised, more explicit prompt** for Prompt 1:

```
Generate a LOW-FIDELITY WIREFRAME (not a website) for an educational desktop application dashboard.

Application Type: Educational lesson planning tool for teachers
Platform: Windows 11 desktop application (not a website)

Screen Type: Dashboard/Home Screen

Wireframe Components (use simple boxes and placeholders):
- Header bar: App title "Bilingual Lesson Planner"
- Main card (large rectangle, centered): Current Lesson Display
  - Text: "Math - 5th Grade"
  - Text: "1:06 PM - 1:47 PM"
  - Large number display: "23:45 remaining"
  - Two button placeholders: "View Full Plan" | "Enter Lesson Mode"
- Two smaller cards below (side by side): Previous Lesson | Next Lesson
- Bottom section: Week calendar grid (Mon-Fri columns, numbers in cells)

Layout Style: Desktop application interface (not website)
Visual Style: Simple wireframe boxes, no colors, no images, just layout structure
Fidelity: Low-fidelity wireframe (boxes, lines, placeholders)

This is for a desktop application, not a marketing website.
```

**Key Changes**:
- Explicitly says "WIREFRAME" not "website"
- Specifies "desktop application" not "website"
- Emphasizes "low-fidelity" and "boxes/placeholders"
- Clarifies educational tool context

---

## Solution 2: Use MockFlow's Manual Tools Instead

If AI continues to fail, **use MockFlow's manual wireframing tools**:

### Step-by-Step Manual Creation:

1. **Start with a Blank Wireframe**
   - Don't use AI generation
   - Use MockFlow's UI packs and templates

2. **Use UI Packs** (Available in Free Tier)
   - Search for "dashboard" templates
   - Look for "desktop application" templates
   - Use "educational" or "admin" UI packs

3. **Build Component by Component**:
   - Drag and drop components
   - Use MockFlow's component library
   - No AI credits needed!

### Recommended UI Packs to Use:
- **Desktop Application UI Pack**
- **Dashboard UI Pack**
- **Admin Panel UI Pack**
- **Educational App UI Pack** (if available)

---

## Solution 3: Simplified, Direct Prompt

Try this **ultra-simple, direct prompt**:

```
Create a wireframe layout for a desktop application dashboard.

Show:
1. Header with app name
2. Large centered card showing current lesson info
3. Two buttons below the card
4. Calendar grid at bottom

Use simple boxes and placeholders. This is a wireframe, not a finished design.
```

**Why This Might Work**:
- Very direct and simple
- No complex descriptions
- Explicitly says "wireframe" and "boxes"
- Focuses on layout, not content

---

## Solution 4: Use MockFlow's Text-to-Wireframe Feature Differently

MockFlow might have **multiple AI features**:

1. **Text-to-Wireframe** (what you want)
2. **Text-to-Website** (what you got)
3. **Template-Based Generation**

### Check MockFlow Interface:
- Look for **"Generate Wireframe"** button (not "Generate Website")
- Check if there's a **dropdown** to select wireframe type
- See if there's a **"Template"** option to start from

---

## Solution 5: Start from Template, Then Use AI

### Hybrid Approach:

1. **Start with a Template**
   - Choose "Dashboard" or "Desktop App" template
   - This gives you the right structure

2. **Then Use AI for Specific Parts**
   - Use AI to generate individual components
   - Example: "Add a lesson card component"
   - Example: "Add a timer display component"

3. **Manual Assembly**
   - Drag components into place
   - Adjust sizes and positions
   - No full-screen AI generation needed

---

## Solution 6: Alternative Tools (If MockFlow AI Fails)

If MockFlow's AI continues to fail, consider:

### Option A: Use MockFlow Manually (No AI)
- **Pros**: Full control, no AI issues, uses UI packs
- **Cons**: Takes more time, but more reliable

### Option B: Use Other Free Tools
- **Figma** (free tier): Has wireframe templates
- **Penpot** (free): Open-source wireframing
- **Miro** (free tier): Has wireframe templates

### Option C: Create Simple Mockups in Code/Design Tools
- Use our planning document as reference
- Create simple boxes/layouts manually
- Share screenshots for feedback

---

## Recommended Next Steps

### Try This Order:

1. **First**: Use Solution 1 (More Explicit Wireframe Prompt)
   - Copy the revised prompt above
   - Try generating again
   - See if it works better

2. **If That Fails**: Use Solution 3 (Simplified Prompt)
   - Try the ultra-simple version
   - See if basic prompt works

3. **If Still Failing**: Use Solution 2 (Manual Tools)
   - Skip AI generation entirely
   - Use MockFlow's UI packs manually
   - Build wireframe component by component

4. **Last Resort**: Use Solution 6 (Alternative Tools)
   - Try Figma or Penpot
   - Or create simple mockups manually

---

## What to Share with Me

Even if the AI generates wrong content, you can still:

1. **Share the Wrong Output**
   - Screenshot what MockFlow generated
   - I can help identify what went wrong
   - We can refine the prompt together

2. **Share Manual Wireframes**
   - If you build manually, share those
   - I can provide feedback and suggestions

3. **Describe What You See**
   - Tell me what MockFlow's interface looks like
   - What options are available
   - I can help navigate the tool

---

## Quick Fix: Try This Prompt Right Now

Copy and paste this **revised prompt**:

```
WIREFRAME for desktop application dashboard (not website).

Simple layout with boxes:
- Top: Header bar with app title
- Center: Large card showing lesson info (subject, time, countdown)
- Below card: Two buttons side by side
- Bottom: Calendar grid (5 columns for weekdays)

Use wireframe style: boxes, lines, placeholders. No colors, no images, just structure.
This is an educational desktop app, not a marketing website.
```

**Why This Should Work**:
- Starts with "WIREFRAME" (explicit)
- Says "desktop application" (not website)
- Emphasizes "boxes, lines, placeholders"
- Ends with clarification (not marketing website)

---

## Understanding MockFlow's AI Behavior

MockFlow's AI might be:
- **Template-biased**: Defaulting to website templates
- **Context-confused**: Not understanding educational vs marketing
- **Mode-specific**: May need to select "wireframe mode" vs "website mode"

**Solution**: Be extremely explicit about:
- ✅ Wireframe (not website)
- ✅ Desktop application (not website)
- ✅ Educational tool (not marketing)
- ✅ Low-fidelity (boxes, not designs)

---

## Alternative: Describe What You See

If you can, tell me:
1. **What MockFlow generated**: Screenshot or description
2. **What options MockFlow shows**: Buttons, dropdowns, settings
3. **What you tried**: Which prompt, which feature

I can help troubleshoot based on what you're seeing!

---

**Next Action**: Try the revised prompt above, or switch to manual wireframing with UI packs.


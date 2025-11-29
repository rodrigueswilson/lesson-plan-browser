# Start Session 5 - Complete Remaining Features

**Quick Context**: The Bilingual Weekly Plan Builder is 79% complete (11/13 features). All core functionality works perfectly. This session completes the final 3 optional features for 100% completion.

---

## 🎯 Session Goal

Implement the 3 remaining features:
1. **Image Preservation** - Extract images from input, re-insert in output
2. **Hyperlink Preservation** - Maintain clickable links in output
3. **Analytics Dashboard** - Visual charts for performance metrics

**Estimated Time**: 4-7 hours (can be split into multiple sessions)

---

## 📋 What You Need to Know

### Current Status
- ✅ App is production-ready and fully functional
- ✅ 11/13 features complete
- ✅ All core workflows working (generate, process, track, manage)
- ✅ Test fixtures already exist in `tests/fixtures/`
- ✅ Performance tracking already collecting data

### What's Missing
- ❌ Images from input are lost in output
- ❌ Hyperlinks become plain text
- ❌ No visual dashboard for analytics (data is collected but not visualized)

---

## 🚀 Quick Start

### Step 1: Review the Plan
Read `NEXT_SESSION_PLAN.md` - it has complete implementation details with code snippets.

### Step 2: Install Dependencies
```bash
cd frontend
npm install recharts
```

### Step 3: Choose Your Path

**Option A - Do Everything (5-6 hours)**:
Start with Part A (Images), then Part B (Hyperlinks), then Part C (Analytics)

**Option B - Images Only (2 hours)**:
Just implement image preservation - most visible user impact

**Option C - Analytics Only (2-3 hours)**:
Just build the dashboard - useful for research

---

## 📁 Key Files to Modify

### For Images & Hyperlinks:
- `tools/docx_parser.py` - Add extraction methods
- `tools/batch_processor.py` - Store in lesson JSON
- `tools/docx_renderer.py` - Add insertion methods

### For Analytics:
- `backend/api.py` - Add `/api/analytics/*` endpoints
- `frontend/src/components/Analytics.tsx` (NEW) - Dashboard component
- `frontend/src/App.tsx` - Integrate analytics section

---

## 💡 Implementation Tips

### Images
- Extract: `rel.target_part.blob` gives you binary data
- Store: `lesson_json['_images']` (underscore = metadata, won't go to LLM)
- Insert: `run.add_picture(BytesIO(data), width=Inches(3.0))`

### Hyperlinks
- Extract: Use XPath `.//w:hyperlink` to find links
- Store: `lesson_json['_hyperlinks']` with text + URL
- Insert: Use `OxmlElement` to create hyperlink with blue, underlined styling

### Analytics
- Backend: `PerformanceTracker` methods already exist from Session 2
- Frontend: Use recharts for charts (pie, bar, line)
- Export: CSV download for research data

---

## ✅ Success Criteria

When done, you'll have:
- [ ] Images preserved from input to output
- [ ] Hyperlinks remain clickable in output
- [ ] Analytics dashboard with 4 cards + 3 charts
- [ ] CSV export working
- [ ] All tests passing
- [ ] 100% feature completion (13/13)

---

## 🎉 After This Session

The app will be **feature-complete** with all 13 planned enhancements:
- ✅ Document Processing (4/4) - including images & hyperlinks
- ✅ Workflow Intelligence (2/2) - "No School" + performance tracking
- ✅ Frontend UX (4/4) - checkboxes, buttons, progress, week detection
- ✅ History & Analytics (3/3) - filters, file ops, dashboard

---

**Ready to start? Let's complete these final features!**

Ask me: "Let's implement [images/hyperlinks/analytics]" or "Let's do everything"

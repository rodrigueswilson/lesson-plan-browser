# Session 5: Complete Remaining Features

**Date**: TBD  
**Status**: READY TO START  
**Estimated Time**: 4-7 hours  
**Priority**: OPTIONAL (App is production-ready without these)

---

## 🎯 Session Objectives

Complete the 3 remaining optional features:
1. **Image Preservation** (2 hours)
2. **Hyperlink Preservation** (2 hours)  
3. **Analytics Dashboard** (2-3 hours)

---

## 📋 Pre-Session Checklist

- [ ] Review python-docx image API: https://python-docx.readthedocs.io/en/latest/user/pictures.html
- [ ] Install recharts: `cd frontend && npm install recharts`
- [ ] Create test fixtures with real images and hyperlinks
- [ ] Backup database

---

## 🖼️ Part A: Image Preservation (2 hours)

### Implementation Files
- `tools/docx_parser.py` - Add `extract_images()` method
- `tools/batch_processor.py` - Store images in `lesson_json['_images']`
- `tools/docx_renderer.py` - Add `_insert_images()` method

### Key Code Snippets

**Extract images** (`docx_parser.py`):
```python
def extract_images(self) -> List[Dict[str, Any]]:
    images = []
    for rel in self.doc.part.rels.values():
        if "image" in rel.target_ref:
            images.append({
                'data': rel.target_part.blob,
                'content_type': rel.target_part.content_type,
                'filename': rel.target_ref.split('/')[-1]
            })
    return images
```

**Insert images** (`docx_renderer.py`):
```python
def _insert_images(self, doc: Document, images: List[Dict]):
    for image in images:
        paragraph = doc.add_paragraph()
        run = paragraph.add_run()
        image_stream = BytesIO(image['data'])
        run.add_picture(image_stream, width=Inches(3.0))
```

### Testing
- Input with image → Output has image
- Multiple images preserved
- No images → Normal rendering

---

## 🔗 Part B: Hyperlink Preservation (2 hours)

### Implementation Files
- `tools/docx_parser.py` - Add `extract_hyperlinks()` method
- `tools/batch_processor.py` - Store links in `lesson_json['_hyperlinks']`
- `tools/docx_renderer.py` - Add `_restore_hyperlinks()` method

### Key Code Snippets

**Extract hyperlinks** (`docx_parser.py`):
```python
def extract_hyperlinks(self) -> List[Dict[str, str]]:
    from docx.oxml.ns import qn
    hyperlinks = []
    for paragraph in self.doc.paragraphs:
        for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
            r_id = hyperlink.get(qn('r:id'))
            if r_id:
                url = paragraph.part.rels[r_id].target_ref
                text = ''.join(node.text for node in hyperlink.xpath('.//w:t'))
                hyperlinks.append({'text': text, 'url': url})
    return hyperlinks
```

**Insert hyperlinks** (`docx_renderer.py`):
```python
def _add_hyperlink(self, paragraph, text: str, url: str):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    
    part = paragraph.part
    r_id = part.relate_to(url, 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink', is_external=True)
    
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    # Add run with blue, underlined text
```

### Testing
- Hyperlinks remain clickable
- Multiple links preserved
- Correct URL and text

---

## 📊 Part C: Analytics Dashboard (2-3 hours)

### Implementation Files
- `backend/api.py` - Add `/api/analytics/*` endpoints
- `frontend/src/components/Analytics.tsx` (NEW) - Dashboard component
- `frontend/src/App.tsx` - Integrate analytics section

### Backend API Endpoints

```python
@app.get("/api/analytics/summary")
async def get_analytics_summary(days: int = 30):
    tracker = get_tracker()
    return tracker.get_aggregate_stats(days)

@app.get("/api/analytics/export")
async def export_analytics(days: int = 30):
    tracker = get_tracker()
    csv_data = tracker.export_to_csv(days)
    return Response(content=csv_data, media_type="text/csv")
```

### Frontend Component Structure

**Analytics.tsx**:
- Summary cards: Total Plans, Avg Time, Total Tokens, Total Cost
- Pie chart: Model distribution
- Bar chart: Operation breakdown (parse/llm/render)
- Line chart: Daily activity
- Export to CSV button

### Install Dependencies
```bash
cd frontend
npm install recharts
```

### Testing
- Dashboard loads correctly
- Charts render with data
- Export CSV works
- Time range selector works

---

## 📊 Timeline

| Task | Time | Status |
|------|------|--------|
| Image extraction | 45 min | Pending |
| Image insertion | 45 min | Pending |
| Image testing | 30 min | Pending |
| Hyperlink extraction | 30 min | Pending |
| Hyperlink insertion | 45 min | Pending |
| Hyperlink testing | 30 min | Pending |
| Analytics API | 30 min | Pending |
| Analytics component | 90 min | Pending |
| Analytics integration | 30 min | Pending |
| **TOTAL** | **5.5 hours** | |

---

## ✅ Success Criteria

- [ ] Images preserved from input to output
- [ ] Hyperlinks remain clickable
- [ ] Analytics dashboard displays metrics
- [ ] All tests passing
- [ ] Code follows project principles (DRY, SSOT, KISS, SOLID, YAGNI)

---

## 📝 Notes

- **Images**: Store as `_images` in lesson JSON (won't be sent to LLM)
- **Hyperlinks**: Store as `_hyperlinks` in lesson JSON
- **Analytics**: Performance data already collected, just needs visualization
- **Testing**: Create real test fixtures with actual images/hyperlinks

---

## 🚀 After Completion

All 13 planned features will be complete:
- ✅ Document Processing (4/4)
- ✅ Workflow Intelligence (2/2)
- ✅ Frontend UX (4/4)
- ✅ History & Analytics (3/3)

**Total**: 13/13 features = 100% completion

---

**Ready to start when you are!**

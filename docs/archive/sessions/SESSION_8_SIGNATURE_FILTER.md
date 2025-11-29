# Session 8 - Content Filtering & Token Optimization

## Problems

### 1. Signature Content
- ❌ Extracted and sent to LLM (wasting tokens)
- ❌ Appearing in output as images/text
- ❌ Not relevant to lesson plan content

### 2. Hyperlink URLs
- ❌ URLs sent to LLM (wasting tokens)
- ❌ LLM doesn't need to see URLs
- ❌ URLs are just metadata to preserve

### 3. No School Days
- ❌ Full LLM-generated content for "No School" days
- ❌ User has to manually delete generated text
- ❌ Waste of tokens and time for days with no instruction

## Solution Implemented

### 1. Signature Detection Pattern Matching

Added `_is_signature_content()` method to detect signature sections:

**Patterns:**
- "I certify"
- "Certification"
- "Teacher signature" / "Principal signature"
- "Aligned with...standards"
- "New Jersey Student Learning" / "NJSLS"
- "Signature:" / "Date:...signature"

### 2. Text Filtering

Modified `get_full_text()` to accept `exclude_signatures` parameter:
- **Default:** `True` (filters out signature content)
- Filters paragraphs before sending to LLM
- **Token savings:** Eliminates unnecessary certification text

### 3. Image Filtering

Modified `extract_images()` to accept `exclude_signatures` parameter:
- **Default:** `True` (filters out signature images)
- Checks image context against signature patterns
- **Token savings:** Prevents signature images from being processed

### 4. URL Stripping

Modified `get_full_text()` and `extract_subject_content()` to accept `strip_urls` parameter:
- **Default:** `True` (removes URLs from text sent to LLM)
- Uses regex to strip `http://` and `https://` URLs
- **Token savings:** URLs can be 50-100+ characters each
- **Hyperlinks preserved:** Extracted separately and re-inserted in output

### 5. Per-Day No School Detection

Added `is_day_no_school()` method and modified `extract_subject_content()`:
- **Detects "No School" per day** instead of entire document
- Patterns: "No School", "Staff Development", "Professional Development", etc.
- **Replaces full day content with "No School" marker**
- **LLM only processes regular instruction days**
- Returns `no_school_days` list for tracking

## Files Modified

### `tools/docx_parser.py`

**Added:**
- `_is_signature_content(text: str) -> bool` - Pattern matching for signatures
- `_get_no_school_patterns() -> list` - Centralized No School patterns
- `is_day_no_school(day_text: str) -> bool` - Per-day No School detection
- `exclude_signatures` parameter to `get_full_text()`
- `exclude_signatures` parameter to `extract_images()`
- `strip_urls` parameter to `get_full_text()`
- `strip_urls` parameter to `extract_subject_content()`
- `no_school_days` field in `extract_subject_content()` return value

**Changes:**
- +100 lines total
- Backward compatible (defaults to filtering)

## Benefits

### Token Savings
- **Before:** Signature text + images + URLs + No School days sent to LLM
- **After:** Only clean lesson content for instruction days sent to LLM
- **Estimated savings per 5-slot processing run:**
  - Signature text: ~50-100 tokens
  - URLs (207 links × ~20 tokens avg): ~4,000 tokens
  - No School days (1 day × ~500 tokens generated): ~500 tokens
  - **Total: ~4,550-4,600 tokens saved per processing run!**
  
**Cost Impact:**
- GPT-4: ~$0.14 saved per run (~$28/month for 200 runs)
- Claude: ~$0.11 saved per run (~$22/month for 200 runs)

### Cleaner Output
- No signature images in "Attached Images" section
- No certification text in output
- **No LLM-generated content for "No School" days**
- User doesn't need to manually delete No School content
- Focus on actual lesson content

### Better Hyperlink Placement
- RapidFuzz already installed (was present)
- Fuzzy matching now active
- Should improve inline placement rate

## Testing

### To Test
1. Restart backend (to load new code)
2. Process a lesson plan with signatures
3. Check output:
   - ✅ No signature images
   - ✅ No certification text
   - ✅ Hyperlinks better placed (with RapidFuzz)

### Expected Results
- Fewer images extracted (signature images excluded)
- Shorter content sent to LLM (~4,600 tokens saved)
- No School days show only "No School" marker
- No LLM-generated content for No School days
- Cleaner output DOCX

## Next Steps

1. **Test with real lesson plan** - Verify signature filtering works
2. **Check hyperlink placement** - Should be improved with RapidFuzz
3. **Monitor token usage** - Should see reduction in LLM costs
4. **Adjust patterns if needed** - Add more signature patterns if some slip through

## Configuration

Both filtering options default to `True` but can be disabled if needed:

```python
# Disable filtering (not recommended)
text = parser.get_full_text(exclude_signatures=False)
images = parser.extract_images(exclude_signatures=False)
```

---

**Status:** Implemented, ready for testing  
**Impact:** Reduced token costs, cleaner output  
**Risk:** Low (backward compatible, defaults to filtering)

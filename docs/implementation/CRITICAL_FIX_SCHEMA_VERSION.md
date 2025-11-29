# CRITICAL FIX: Schema Version in Batch Processor

**Date:** 2025-10-19  
**Issue:** Coordinate-based placement not being used in production  
**Status:** ✅ FIXED

---

## 🔍 Problem Discovered

### **Hyperlink Journey Tracking Revealed:**

When tracking hyperlinks from input to output, we found:

**Daniela W43:**
- 1 table link → paragraph link (should have been 0)

**Wilson W43:**
- 725 table links → paragraph links (should have been 0!)
- Only 120 table links stayed as table links

This meant **coordinate placement was NOT being used** in production!

---

## 🐛 Root Cause

### **Found in `batch_processor.py` line 552:**

```python
# OLD CODE (WRONG):
lesson_json["_media_schema_version"] = "1.1"
```

The batch processor was setting schema version to `"1.1"` instead of `"2.0"`.

### **Impact:**

When the renderer received `_media_schema_version: "1.1"`:
- It used the OLD fuzzy matching logic
- It did NOT use the NEW coordinate-based placement
- Links were placed using context matching (lower success rate)
- Many links ended up in fallback section

---

## ✅ Solution

### **Fixed in `batch_processor.py` line 552:**

```python
# NEW CODE (CORRECT):
lesson_json["_media_schema_version"] = "2.0"  # Use v2.0 for coordinate placement
```

Now the renderer will:
- Detect schema version `"2.0"`
- Use coordinate-based placement
- Achieve 100% placement rate for table links
- Minimize fallback links

---

## 📊 Expected Impact

### **Before Fix (Schema v1.1):**

**Wilson W43 (as tested):**
- Table links: 158 in input
- Placed inline: 120 (76%)
- In fallback: 38 (24%)
- Method: Fuzzy matching

### **After Fix (Schema v2.0):**

**Wilson W43 (expected):**
- Table links: 158 in input
- Placed inline: 158 (100%)
- In fallback: 0 (0%)
- Method: Coordinate placement

**Improvement: +24 percentage points for table links!**

---

## 🎯 Why This Happened

### **Timeline:**

1. **Phase 1:** We enhanced the parser to capture coordinates (schema v2.0)
2. **Phase 2:** We enhanced the renderer to use coordinates (schema v2.0)
3. **Testing:** We manually set schema to v2.0 in test scripts
4. **Production:** Batch processor was still using v1.1 (not updated)

### **The Gap:**

We updated the parser and renderer but **forgot to update the batch processor** to use the new schema version.

---

## ✅ Verification Needed

### **Next Steps:**

1. **Re-generate lesson plans** with the fixed batch processor
2. **Track hyperlinks** again to verify:
   - All table links stay as table links
   - 100% coordinate placement
   - Zero table→paragraph transformations
3. **Compare results** before and after fix

### **Expected Results:**

**Daniela W43:**
- Before: 47/48 inline (97.9%)
- After: 47/48 inline (97.9%) - same (only 1 paragraph link in input)

**Wilson W43:**
- Before: 120/207 inline (58.0%)
- After: 158/207 inline (76.3%) - **+18.3 percentage points!**
- (87 paragraph links will still go to fallback - expected)

---

## 📝 Lessons Learned

### **1. Test the Full Pipeline**

We tested:
- ✅ Parser in isolation
- ✅ Renderer in isolation
- ❌ Full pipeline (batch processor → renderer)

**Lesson:** Always test the complete end-to-end flow, not just individual components.

### **2. Schema Version is Critical**

The schema version acts as a "feature flag":
- v1.1 = fuzzy matching
- v2.0 = coordinate placement

**Lesson:** Ensure all components use the same schema version.

### **3. Production Validation is Essential**

Our isolated tests showed 100% success, but production showed issues.

**Lesson:** Always validate in the actual production environment.

---

## 🚀 Deployment

### **Files Changed:**

- `tools/batch_processor.py` (1 line changed)

### **Change:**

```diff
- lesson_json["_media_schema_version"] = "1.1"
+ lesson_json["_media_schema_version"] = "2.0"  # Use v2.0 for coordinate placement
```

### **Risk Assessment:**

- **Risk Level:** LOW
- **Breaking Changes:** None
- **Backward Compatibility:** Yes (v1.1 still works if needed)
- **Testing Required:** Re-generate lesson plans and verify

---

## 📊 Success Criteria

### **After deploying this fix:**

- [x] Batch processor sets schema to v2.0
- [ ] Re-generate Daniela W43 (verify same results)
- [ ] Re-generate Wilson W43 (verify improvement)
- [ ] Track hyperlinks (verify no table→paragraph)
- [ ] Confirm 100% table link placement
- [ ] Validate in production

---

## 🎉 Conclusion

**This was a simple but critical fix:**
- Changed 1 line of code
- Enables coordinate-based placement in production
- Expected to improve table link placement by ~24 percentage points
- No breaking changes
- Ready to deploy

**Status:** ✅ FIXED - Ready for re-testing

---

**Next Action:** Re-generate lesson plans and verify the fix works!

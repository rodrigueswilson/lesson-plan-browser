# ADR 001: Hyperlink Placement Strategy

**Status:** Accepted  
**Date:** 2025-10-19  
**Decision Makers:** Development team + Other AI (collaborative review)  
**Stakeholders:** Teachers, users of Bilingual Weekly Plan Builder  

---

## Context

The Bilingual Weekly Plan Builder transforms English lesson plans into bilingual English-Portuguese documents. During this transformation, hyperlinks from the input must be placed in the output document. Currently, 34.4% of hyperlinks are placed inline, while 65.6% fall back to a "Referenced Links" section at the end of the document.

**Problem:** Teachers may prefer more links inline for easier access, but we need to balance this with accuracy and avoid false positives (links in wrong cells).

---

## Decision

**We will implement ONLY a fuzzy matching threshold change (0.65 → 0.55) with comprehensive monitoring.**

**We will DEFER:**
- Parser enhancement (curriculum row detection)
- Coordinate-based placement
- "Keep links in cells" strategy

**We will REQUIRE:**
- Teacher feedback before major UX changes
- Manual validation of all changes
- Telemetry to measure real impact

---

## Rationale

### **Why Threshold Change?**

**Evidence:**
- Research-validated approach (Towards Data Science, Aerospike, RapidFuzz docs)
- Simple, reversible change (feature flag)
- Expected +10-15% improvement (conservative)
- Industry standard: 0.55 is "moderate similarity" range

**Pros:**
- ✅ Low risk (easy to revert)
- ✅ Proven technique
- ✅ Measurable impact
- ✅ Fast implementation (2 hours)

**Cons:**
- ⚠️ May increase false positives (mitigated by monitoring)
- ⚠️ Limited improvement (~10-15%, not 25-35%)

---

### **Why DEFER Parser Enhancement?**

**Initial assumption:** Enhancing parser to detect curriculum rows would fix 28.9% missing hints → 90%+ coverage.

**Reality (from pre-implementation audit):**
- Only 32% of missing hints are curriculum patterns (LESSON, UNIT, GUIDE)
- 68% are generic activity/resource names ("Cool Down", "Force and Motion", "Item UIN")
- Parser enhancement would only improve coverage from 71.1% → ~80% (not 90%+)

**Decision:** Not worth 2 hours implementation for 9% gain. Need different approach (context-based, teacher tags) for the 68% generic links.

**Future consideration:** Revisit if we develop context-based inference or teacher tagging system.

---

### **Why REJECT Coordinate-Based Placement?**

**Proposal:** Capture table coordinates (row/col indices) during parsing, use them for placement.

**Analysis:**
- **Assumption:** Input and output templates are structurally identical
- **Reality:** Input is English-only, output is bilingual (transformed by LLM)
- **Evidence:** Templates vary by teacher, LLM may reorder sections
- **Conclusion:** Coordinates from input won't map to output reliably

**Why it won't work:**
- Input/output are different structures (not 1:1 mapping)
- Bilingual text is longer (row counts differ)
- LLM transformation may reorder content
- Would mostly fall back to existing logic anyway

**Decision:** Coordinate approach is too brittle for bilingual transformation use case.

---

### **Why DEFER "Keep Links in Cells" Strategy?**

**Proposal:** Place all links in their target cells (inline or at end of cell), avoid "Referenced Links" section.

**Analysis:**
- **Assumption:** Teachers prefer links in cells vs. end of document
- **Reality:** No teacher feedback collected yet
- **Risks:** Cell clutter (8+ links in some cells), readability issues with bilingual text

**Validation revealed:**
- Text-based grouping doesn't work (63.6% unclassified)
- Templates vary (can't hardcode row mapping)
- Need dynamic detection (adds complexity)
- No evidence teachers want this

**Decision:** Get teacher feedback FIRST, then decide if this UX change is wanted.

**Future consideration:** If teachers request it, implement with:
- Overflow handling (max 5-6 links per cell)
- Dynamic template detection
- Grouped presentation (Curriculum, Activities, etc.)

---

## Consequences

### **Positive:**

1. **Simple, proven approach** - Threshold change is well-understood
2. **Low risk** - Easy to revert if issues arise
3. **Measurable** - Telemetry shows real impact
4. **Fast** - 2 hours implementation vs. weeks for alternatives
5. **Evidence-based** - Research validates approach

### **Negative:**

1. **Limited improvement** - Only +10-15% (not 25-35%)
2. **Doesn't solve root cause** - 68% missing hints still unfixable
3. **May increase FPs** - Need monitoring to catch issues
4. **Defers bigger improvements** - Parser/UX changes postponed

### **Neutral:**

1. **Teacher feedback required** - Must schedule within 2 weeks
2. **Monitoring overhead** - Daily check-ins for 1 week
3. **Manual validation** - 2 hours per deployment

---

## Alternatives Considered

### **Alternative 1: Parser Enhancement First**

**Pros:** Fixes root cause (missing hints)  
**Cons:** Only 32% of missing hints, 2 hours work for 9% gain  
**Decision:** Defer until better approach available  

### **Alternative 2: Coordinate-Based Placement**

**Pros:** Theoretically precise if templates match  
**Cons:** Templates don't match (input ≠ output), too brittle  
**Decision:** Reject for this use case  

### **Alternative 3: "Keep Links in Cells"**

**Pros:** May improve UX (if teachers want it)  
**Cons:** No validation, adds complexity, risks clutter  
**Decision:** Defer until teacher feedback collected  

### **Alternative 4: Do Nothing**

**Pros:** Zero risk, zero effort  
**Cons:** Misses opportunity for proven improvement  
**Decision:** Reject - threshold change is low-risk, high-value  

---

## Implementation

### **Phase 1: Foundation (2 hours)**
1. Fix input/output pairing logic (prerequisite)
2. Add threshold constant + logging
3. Add fallback counter

### **Phase 2: Validation (2 hours)**
1. Manual validation on 3 files (high/medium/low baseline)
2. Document results (TP/FP/TN/FN rates)
3. Decision: proceed or abort

### **Phase 3: Monitor (1 week)**
1. Deploy to production
2. Process 10-20 files
3. Daily monitoring
4. Revert if FP rate >8%

### **Phase 4: Feedback (Week 2)**
1. Schedule teacher sessions
2. Show mockups (3 versions)
3. Collect preferences
4. Document findings

### **Phase 5: Decision (Week 3)**
1. Review all data
2. Decide: keep/adjust/revert
3. Document outcome
4. Plan next steps

---

## Success Metrics

### **Must Achieve:**
- Inline placement ≥ 45% (from 34.4%)
- False positive rate ≤ 5%
- Zero broken links
- No teacher complaints

### **Revert If:**
- FP rate >8%
- Teacher complaints about wrong links
- Broken links
- Links in obviously wrong cells

---

## References

### **Research:**
- [Towards Data Science: FuzzyWuzzy - the Before and After](https://towardsdatascience.com/fuzzywuzzy-the-before-and-after-c3661ea62ef8/)
- [Aerospike: What is Fuzzy Matching?](https://aerospike.com/blog/fuzzy-matching/)
- [RapidFuzz Documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html)

### **Internal Documents:**
- Pre-implementation audit results (`pre_implementation_audit_results.json`)
- Diagnostic analysis (`hyperlink_diagnostic.csv`)
- Validation framework (`SESSION_10_HYPERLINK_STRATEGY_VALIDATION.md`)
- Consensus summary (`CONSENSUS_SUMMARY.md`)

### **Key Findings:**
- 71.1% have complete metadata (section_hint + day_hint)
- 28.9% missing section_hint (only 32% fixable with parser)
- 34.4% current inline placement rate
- 63.6% of links can't be classified by text patterns

---

## Review History

- **2025-10-19:** Initial decision
- **Reviewed by:** Other AI (collaborative analysis)
- **Next review:** After 1 week monitoring + teacher feedback

---

## Notes

**Key lesson:** Validate assumptions with data BEFORE implementation. Pre-implementation audit revealed:
- Parser enhancement would only fix 32% (not 90%)
- Simulation pairing was broken (results unreliable)
- Most missing hints are generic (can't be pattern-matched)

**This prevented wasting 6+ hours on low-ROI work.**

**Collaborative review with Other AI was essential** - caught flawed assumptions, demanded empirical validation, pushed for realistic expectations.

---

**Status:** Ready for implementation pending user approval

# Session 9 - Hyperlink Preservation Research Plan

## Problem Statement

**Issue:** Hyperlinks are being extracted correctly but not placed inline in the output DOCX. Instead, they appear in a "Referenced Links" section at the end.

**Root Cause:** The LLM transforms/rephrases the original content during bilingual lesson plan generation, so the exact hyperlink text no longer exists in the output. Even fuzzy matching (RapidFuzz) can't find good matches because the content is completely rewritten.

**Example:**
- **Original:** "LESSON 5: REPRESENT PRODUCTS AS AREAS" (hyperlink)
- **LLM Output:** "Lección 5: Representar productos como áreas" (rephrased, bilingual)
- **Result:** Fuzzy match score < 65%, link goes to "Referenced Links"

---

## Current Implementation

### What Works
- ✅ Hyperlink extraction (100% success rate)
- ✅ Structure-based placement for images (works perfectly)
- ✅ RapidFuzz fuzzy matching (installed and working)
- ✅ Fallback to "Referenced Links" section (preserves all links)

### What Doesn't Work
- ❌ Inline placement rate: ~10-20% (target: 70-90%)
- ❌ LLM ignores "preserve exact phrases" instructions
- ❌ Curriculum resource links get completely rephrased

### Current Matching Strategy
1. **Exact text match** - Rarely works (LLM rephrases everything)
2. **Fuzzy context match** (65% threshold) - Low success due to bilingual transformation
3. **Structure hints** (day + section) - Not enough signal
4. **Fallback** - "Referenced Links" section

---

## Research Questions

### Question 1: How do other DOCX transformation tools handle hyperlinks?
**Search queries:**
- "preserve hyperlinks during document transformation"
- "python-docx hyperlink preservation after LLM processing"
- "maintain hyperlinks when rephrasing content"
- "docx hyperlink anchoring strategies"

**Tools to investigate:**
- Pandoc (document conversion)
- Mammoth (DOCX to HTML)
- docx2python
- python-docx-template

### Question 2: How do translation tools preserve links?
**Search queries:**
- "translation memory hyperlink preservation"
- "CAT tools hyperlink handling"
- "Google Translate API preserve links"
- "DeepL API maintain hyperlinks"

**Hypothesis:** Translation tools face the same problem - they might have solved it.

### Question 3: Can we use semantic embeddings for better matching?
**Search queries:**
- "semantic similarity for text anchoring"
- "sentence transformers for fuzzy matching"
- "embedding-based hyperlink placement"
- "vector similarity for document alignment"

**Approach:**
- Use sentence embeddings (e.g., sentence-transformers)
- Compare original hyperlink context vs. output text
- Find semantically similar locations even if text is different

### Question 4: Can we mark hyperlinks for LLM preservation?
**Search queries:**
- "LLM preserve specific text patterns"
- "GPT-4 maintain hyperlinks in output"
- "prompt engineering preserve links"
- "XML tags in LLM prompts"

**Approaches to test:**
- Wrap links in special markers: `[[LINK:text]]`
- Use XML/HTML tags: `<a href="...">text</a>`
- Provide links as separate metadata with IDs
- Post-process: Extract links from LLM, match by ID

### Question 5: What do Microsoft Word add-ins do?
**Search queries:**
- "Word add-in preserve hyperlinks during transformation"
- "Office.js hyperlink manipulation"
- "Word VBA hyperlink preservation"
- "OOXML hyperlink relationship management"

**Hypothesis:** Word add-ins that transform content might have solved this.

---

## Proposed Solutions to Test

### Solution A: Semantic Embedding Matching
**Complexity:** Medium  
**Success Probability:** High (70%)

**Approach:**
1. Install `sentence-transformers` library
2. Generate embeddings for hyperlink context
3. Generate embeddings for all paragraphs in output
4. Find best semantic match using cosine similarity
5. Place hyperlink in most similar location

**Pros:**
- Works even when text is completely rephrased
- Language-agnostic (works for bilingual content)
- Proven technology

**Cons:**
- Requires additional library (~500MB model)
- Slower processing (~1-2 seconds per document)
- May need GPU for speed

**Code sketch:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Get embedding for hyperlink context
link_embedding = model.encode(hyperlink['context_snippet'])

# Get embeddings for all output paragraphs
para_embeddings = model.encode(all_output_paragraphs)

# Find best match
similarities = cosine_similarity([link_embedding], para_embeddings)
best_match_idx = similarities.argmax()
```

---

### Solution B: Link ID System
**Complexity:** High  
**Success Probability:** Medium (50%)

**Approach:**
1. Before LLM: Replace hyperlinks with unique IDs: `[LINK_001]`, `[LINK_002]`
2. Send to LLM with instruction: "Preserve all [LINK_XXX] markers"
3. After LLM: Find `[LINK_XXX]` in output, replace with actual hyperlink
4. If LLM removed markers, fall back to semantic matching

**Pros:**
- Simple concept
- Works if LLM cooperates
- Easy to implement

**Cons:**
- LLM might remove/rephrase markers
- Requires LLM instruction compliance
- Fallback still needed

**Code sketch:**
```python
# Before LLM
content_with_ids = content
for i, link in enumerate(hyperlinks):
    content_with_ids = content_with_ids.replace(
        link['text'], 
        f"[LINK_{i:03d}]"
    )

# After LLM
for i, link in enumerate(hyperlinks):
    if f"[LINK_{i:03d}]" in llm_output:
        # Replace with actual hyperlink
        place_hyperlink_at_marker(llm_output, f"[LINK_{i:03d}]", link)
```

---

### Solution C: Two-Pass LLM Strategy
**Complexity:** High  
**Success Probability:** Medium (60%)

**Approach:**
1. **Pass 1:** Send content to LLM, ask it to identify where hyperlinks should go
   - Input: Original content + list of hyperlink texts
   - Output: JSON mapping of {hyperlink_text: target_location_description}
2. **Pass 2:** Use mapping to place hyperlinks in transformed output

**Pros:**
- Leverages LLM's understanding of content
- More accurate than fuzzy matching
- Can handle complex transformations

**Cons:**
- 2x LLM calls = 2x cost
- Slower processing
- LLM might hallucinate locations

---

### Solution D: Lower Fuzzy Match Threshold + Boost Strategies
**Complexity:** Low  
**Success Probability:** Medium (40%)

**Approach:**
1. Lower fuzzy match threshold from 65% to 40%
2. Add boosting for partial word matches
3. Add boosting for same section/day
4. Add penalty for mismatched section/day

**Pros:**
- Easy to implement
- No new dependencies
- Fast

**Cons:**
- May create false positives
- Won't solve fundamental rephrasing issue
- Band-aid solution

**Code changes:**
```python
# Current
if context_score >= 0.65:
    return (context_score, 'fuzzy_context')

# Proposed
if context_score >= 0.40:
    # Boost for word overlap
    words_original = set(hyperlink['text'].lower().split())
    words_output = set(cell_text.lower().split())
    word_overlap = len(words_original & words_output) / len(words_original)
    
    boosted_score = context_score + (word_overlap * 0.2)
    return (min(1.0, boosted_score), 'fuzzy_boosted')
```

---

### Solution E: Accept "Referenced Links" as Feature
**Complexity:** None  
**Success Probability:** 100%

**Approach:**
- Keep current behavior
- Improve "Referenced Links" section formatting
- Add note: "Links preserved from original lesson plans"

**Pros:**
- No development needed
- 100% link preservation
- No false positives
- Teachers can still access all links

**Cons:**
- Links not inline (user requirement)
- Less convenient for teachers

---

## Recommended Research Path

### Day 1 (Tomorrow): Research & Prototyping
1. **Morning (2 hours):** Research Questions 1-3
   - Search for existing solutions
   - Read documentation of similar tools
   - Check academic papers on document alignment

2. **Afternoon (3 hours):** Prototype Solution A (Semantic Embeddings)
   - Install sentence-transformers
   - Test on sample hyperlinks
   - Measure accuracy vs. current fuzzy matching
   - Benchmark performance impact

3. **Evening (1 hour):** Prototype Solution D (Improved Fuzzy Matching)
   - Lower threshold, add boosting
   - Test on real lesson plans
   - Compare with Solution A

### Day 2: Implementation & Testing
1. Implement best solution from prototypes
2. Test on all lesson plans
3. Measure inline placement rate
4. Optimize performance if needed

---

## Success Metrics

**Target:** 70-90% inline placement rate

**Current:** ~10-20% inline placement rate

**Measurement:**
- Count total hyperlinks extracted
- Count hyperlinks placed inline
- Count hyperlinks in "Referenced Links"
- Calculate: inline_rate = inline / total

**Acceptable outcomes:**
- **Best:** 70%+ inline (Solution A or C)
- **Good:** 50-70% inline (Solution B or D)
- **Acceptable:** Keep current + improve formatting (Solution E)

---

## Questions for Other AIs

### For ChatGPT/Claude/Gemini:
1. "I'm building a system that transforms lesson plans using an LLM. The LLM rephrases content, which breaks hyperlink anchoring. How can I preserve hyperlink locations when the text is completely rewritten?"

2. "What's the best way to match hyperlinks from original text to LLM-transformed text when the content is rephrased? Should I use semantic embeddings, fuzzy matching, or something else?"

3. "Has anyone solved the problem of preserving hyperlinks during LLM-based document transformation? What strategies work?"

### For Stack Overflow Search:
- "preserve hyperlinks after text transformation"
- "python docx hyperlink anchoring"
- "semantic similarity for text alignment"
- "fuzzy matching for document transformation"

### For GitHub Search:
- Search repos: `python-docx hyperlink`
- Search repos: `LLM document transformation`
- Search repos: `semantic text matching`

---

## Fallback Plan

If no solution achieves 70%+ inline rate:

**Option 1:** Hybrid approach
- Use best solution for high-confidence matches (>70% similarity)
- Put low-confidence matches in "Referenced Links"
- Show both inline + referenced links

**Option 2:** User configuration
- Add setting: "Hyperlink placement strategy"
  - Aggressive (40% threshold, more false positives)
  - Conservative (65% threshold, fewer inline)
  - Referenced only (current fallback)

**Option 3:** Manual review mode
- Show hyperlink placement suggestions in UI
- Let user approve/reject placements
- Learn from user feedback

---

## Files to Review Tomorrow

1. `tools/docx_renderer.py` - Current matching logic (lines 877-922)
2. `tools/docx_parser.py` - Hyperlink extraction (lines with `extract_hyperlinks`)
3. Research papers on document alignment
4. sentence-transformers documentation
5. python-docx advanced hyperlink examples

---

## Status: Ready for Research

**Next session:** Start with Research Questions 1-3, then prototype Solution A (Semantic Embeddings)

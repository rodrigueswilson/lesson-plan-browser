# Co-Teaching Models for Bilingual Education

Co-teaching model definitions, selection algorithms, and integration with bilingual teaching strategies based on the Friend & Cook framework adapted for multilingual learners.

## Overview

This directory contains resources for integrating co-teaching models into the bilingual lesson plan transformation system. Co-teaching is essential for effective bilingual education delivery, allowing the bilingual teacher and primary teacher to collaborate in supporting multilingual learners.

## Files

### **co_teaching_models.json**
Comprehensive co-teaching model definitions with bilingual education adaptations.

**Contents:**
- 6 co-teaching models (Friend & Cook framework)
- Bilingual advantages for each model
- Compatible bilingual strategies
- WIDA proficiency fit scores
- Implementation requirements
- Lesson context mappings

### **co_teaching_models.csv**
Original co-teaching models reference (Friend & Cook).

**Models:**
1. One Teach, One Observe
2. One Teach, One Assist
3. Parallel Teaching
4. Station Teaching
5. Alternative Teaching
6. Team Teaching

### **co_teaching_strategies.pdf**
Visual reference guide for co-teaching strategies (757KB).

### **portuguese_misconceptions.json**
High-frequency Portuguese→English interference patterns for linguistic misconception prediction.

**Contents:**
- 6 common interference patterns (subject pronouns, adjective placement, past tense -ed, prepositions, false cognates)
- Trigger keywords for pattern matching
- Linguistic notes explaining the interference
- Prevention tips aligned with bilingual strategies
- Default reminder for lessons without specific matches

**Usage:** Simple keyword matching on lesson objectives/vocabulary to provide targeted linguistic warnings in the Misconceptions row.

## Co-Teaching Models for Bilingual Education

### Priority Ranking for Bilingual Co-Teaching

#### Tier 1: High-Impact Models
1. **Team Teaching** - Both teachers co-deliver, models translanguaging
2. **Station Teaching** - Language-focused stations with differentiation
3. **Alternative Teaching** - Targeted intervention by proficiency level

#### Tier 2: Supportive Models
4. **Parallel Teaching** - Smaller groups, increased speaking opportunities
5. **One Teach, One Assist** - Real-time language scaffolding

#### Tier 3: Observational Model
6. **One Teach, One Observe** - Data collection for planning

### Model Selection Factors

**Lesson Context:**
- Subject area and content complexity
- Vocabulary density
- Lesson type (introduction, practice, review)
- Grade cluster

**Student Profile:**
- WIDA proficiency distribution
- Class size
- Student independence level
- Mixed proficiency range

**Bilingual Strategy Compatibility:**
- Which strategies are selected
- L1 integration mode required
- Delivery mode preferences

**Practical Constraints:**
- Planning time available
- Teacher relationship maturity
- Classroom space configuration
- Materials availability

## Integration with Bilingual Strategies

### Strategy-Model Compatibility Matrix

**Translanguaging:**
- ✅✅✅ Team Teaching (95% fit) - Both teachers model code-switching
- ✅✅ Alternative Teaching (85% fit) - Intensive L1/L2 work in small group
- ✅ Station Teaching (75% fit) - One station translanguaging-focused

**Preview-Review:**
- ✅✅✅ Alternative Teaching (95% fit) - Perfect for pre-teaching
- ✅✅ Team Teaching (85% fit) - One teacher previews, other reviews
- ✅ Parallel Teaching (70% fit) - One group gets preview, other review

**Station Teaching Strategies:**
- ✅✅✅ Explicit Vocabulary (95% fit)
- ✅✅✅ Graphic Organizers (90% fit)
- ✅✅✅ Sentence Frames (90% fit)
- ✅✅ Cognate Awareness (85% fit)

**Alternative Teaching Strategies:**
- ✅✅✅ Cognate Awareness (95% fit)
- ✅✅✅ Contrastive Analysis (95% fit)
- ✅✅✅ The Bridge (90% fit)
- ✅✅ Heritage Language Connections (85% fit)

## WIDA Proficiency Considerations

### Proficiency Distribution Impact

**High % Levels 1-2 (Entering/Emerging):**
- **Recommended:** Alternative Teaching (pre-teaching), Team Teaching (dual support)
- **Rationale:** Need intensive L1 support and comprehensible input

**Balanced Levels 2-4 (Emerging-Expanding):**
- **Recommended:** Station Teaching, Parallel Teaching
- **Rationale:** Benefit from differentiated small groups

**High % Levels 5-6 (Bridging/Reaching):**
- **Recommended:** Team Teaching (complex discourse), Alternative Teaching (enrichment)
- **Rationale:** Can handle sophisticated bilingual discourse

**Mixed Levels 1-6:**
- **Recommended:** Station Teaching (proficiency-based stations), Team Teaching (differentiated in real-time)
- **Rationale:** Need flexible differentiation

## Implementation Requirements

### Planning Time by Model

| Model | Planning Time/Week | Coordination Intensity |
|-------|-------------------|----------------------|
| Team Teaching | 60-90 minutes | Very High |
| Station Teaching | 90-120 minutes | Very High |
| Alternative Teaching | 45-60 minutes | Medium |
| Parallel Teaching | 45-60 minutes | Medium |
| One Teach, One Assist | 30-45 minutes | Low |
| One Teach, One Observe | 30-45 minutes | Low |

### Teacher Relationship Maturity

**Established Partnership (1+ year together):**
- Ready for: Team Teaching, Station Teaching
- Characteristics: Trust, shared philosophy, smooth coordination

**Developing Partnership (1 semester together):**
- Ready for: Alternative Teaching, Parallel Teaching
- Characteristics: Building rapport, learning each other's styles

**New Partnership (< 1 semester):**
- Start with: One Teach/One Assist, One Teach/One Observe
- Characteristics: Getting to know each other, establishing roles

### Classroom Setup Requirements

**Team Teaching:**
- Both teachers visible to all students
- Shared board/screen space
- Flexible positioning

**Station Teaching:**
- 3 distinct areas with clear boundaries
- Materials organized by station
- Visual rotation schedule

**Alternative Teaching:**
- Main instructional area
- Separate small group space (table, carpet area, corner)
- Minimal distractions between areas

**Parallel Teaching:**
- Room divided into 2 sections
- Adequate separation to minimize distraction
- Equivalent visibility/resources in each section

## Usage in Lesson Plan System

### Current Integration Status

**Phase 1: Research & Planning** ✅ (Current)
- Co-teaching models documented
- Bilingual adaptations identified
- Selection criteria defined

**Phase 2: Data Structure** 🔄 (In Progress)
- JSON schema designed
- Compatibility matrices created
- Algorithm framework outlined

**Phase 3: Algorithm Implementation** ⏳ (Pending)
- Selection algorithm coded
- Scoring rubric validated
- Edge cases identified

**Phase 4: Prompt Integration** ⏳ (Pending)
- Add Phase 3 to prompt engine
- Output format enhanced
- Co-teaching recommendations generated

**Phase 5: UI Integration** ⏳ (Pending)
- Model selector in app
- Visual recommendations
- Implementation guidance

### How It Will Work

1. **Input:** Primary teacher lesson plan + student proficiency data
2. **Processing:**
   - Phase 1: Load relevant strategy categories
   - Phase 2: Select bilingual strategies
   - **Phase 3: Recommend co-teaching model** (NEW)
   - Phase 4: Create assessment overlay
3. **Output:** Enhanced lesson plan with:
   - Selected bilingual strategies
   - **Recommended co-teaching model**
   - **Implementation guidance**
   - **Role definitions for each teacher**
   - **Setup instructions**
   - **Timing coordination**

### Example Output

```markdown
**Co-Teaching Model:** Station Teaching

**Rationale:** 
- Mixed proficiency levels (Levels 1-4) benefit from differentiated stations
- Vocabulary-heavy lesson aligns with station-based explicit vocabulary strategy
- 45-minute session allows 3 rotations of 12 minutes each

**Station Configuration:**

**Station 1 - Bilingual Teacher (Vocabulary Focus):**
- Explicit vocabulary instruction with cognate awareness
- Portuguese-English word wall building
- Levels 1-2 focus with heavy L1 support
- Materials: Bilingual word cards, cognate chart

**Station 2 - Primary Teacher (Content Application):**
- Guided practice with sentence frames
- Graphic organizer completion
- Levels 3-4 focus with structured support
- Materials: Sentence frame templates, graphic organizers

**Station 3 - Independent Practice:**
- Bilingual reading with comprehension questions
- Word sort activity (cognates vs. false friends)
- Levels 5-6 extension available
- Materials: Bilingual texts, word sort cards, answer keys

**Rotation Schedule:**
- 0-12 min: Group A→Station 1, Group B→Station 2, Group C→Station 3
- 12-24 min: Group A→Station 2, Group B→Station 3, Group C→Station 1
- 24-36 min: Group A→Station 3, Group B→Station 1, Group C→Station 2
- 36-45 min: Whole group debrief and assessment

**Setup Requirements:**
- 3 distinct areas marked with signs
- Timer visible to all students
- Rotation chart posted
- Materials pre-organized at each station
```

## Research Foundation

### Key Sources

**Friend & Cook Framework:**
- Friend, M., & Cook, L. (2017). *Interactions: Collaboration skills for school professionals* (8th ed.)
- Cook, L., & Friend, M. (1995). Co-teaching: Guidelines for creating effective practices

**Bilingual Co-Teaching:**
- Honigsfeld, A., & Dove, M. G. (2010). *Collaboration and co-teaching: Strategies for English learners*
- Dove, M. G., & Honigsfeld, A. (2018). *Co-teaching for English learners: A guide to collaborative planning*

**WIDA Integration:**
- NYSED (2022). Topic Brief #4: Seven Models of Co-Teaching
- Colorín Colorado. Co-Teaching ELLs: 8 Strategies for Success

### Research Gaps

Areas needing further investigation:
1. Optimal co-teaching models for specific WIDA proficiency distributions
2. Bilingual strategy effectiveness across different co-teaching models
3. Planning time requirements in bilingual co-teaching contexts
4. Impact of teacher language proficiency on model selection
5. Student outcomes by co-teaching model in bilingual settings

## Next Steps

### Immediate (Weeks 1-2)
- [ ] Complete `co_teaching_models.json` with full model definitions
- [ ] Review integration plan with bilingual teachers
- [ ] Begin literature review on bilingual co-teaching

### Short-Term (Weeks 3-6)
- [ ] Design and validate selection algorithm
- [ ] Add co-teaching compatibility to all 33 bilingual strategies
- [ ] Create algorithm testing framework

### Medium-Term (Weeks 7-12)
- [ ] Integrate into prompt engine (Phase 3)
- [ ] Pilot with sample lesson plans
- [ ] Gather teacher feedback

### Long-Term (Weeks 13+)
- [ ] Full system integration
- [ ] UI implementation
- [ ] Formal research study

## Contributing

When adding or modifying co-teaching models:
1. Maintain alignment with Friend & Cook framework
2. Include bilingual education adaptations
3. Specify WIDA proficiency fit
4. List compatible bilingual strategies
5. Provide implementation requirements
6. Update selection algorithm accordingly

## Related Documentation

- **[Integration Plan](../docs/co_teaching_integration_plan.md)** - Comprehensive integration strategy
- **[Architecture](../docs/architecture_001.md)** - System architecture
- **[Strategy Pack](../strategies_pack_v2/)** - Bilingual strategies
- **[WIDA Files](../wida/)** - WIDA framework and adaptations
- **[Prompt Engine](../prompt_v4.md)** - Transformation prompt

---

**Status:** Research & Planning Phase  
**Version:** 1.0  
**Last Updated:** 2025-10-04

# Changelog
All notable changes to the Bilingual Weekly Plan Builder.

## [Unreleased] - 2025-11-21

### Added
- `backend/migrations/upgrade_lesson_steps_table.py` for migrating legacy SQLite `lesson_steps` rows to the new schema.
- `tests/test_lesson_steps_api.py` integration coverage to verify `/api/lesson-steps/generate` plus retrieval returns structured JSON data.

### Changed
- `sql/create_lesson_steps_table_supabase.sql` now mirrors the upgraded schema (JSONB columns + timestamp defaults); run manually inside Supabase after deployment.
- `/api/lesson-steps/generate` returns persisted rows so `LessonStepResponse` validation succeeds and clients see accurate timestamps.
- `backend/models_slot.py` now re-exports the canonical `BatchProcessRequest` definition from `backend/models.py` to maintain a single source of truth.

## [1.0.0] - 2025-10-05 (Production Ready)

### Changed - 2025-10-05 (Day 8: Cleanup & Documentation)

#### Repository Organization
- **File Decluttering:** Moved 70+ documentation files to organized structure
- **Directory Structure:** Created `docs/` subdirectories (sessions, progress, phases, archive, guides, training, deployment, security)
- **Root Cleanup:** Reduced root directory from 80+ files to 10 essential files
- **Tool Archiving:** Moved 8 unused tools to `tools/archive/`
- **Test Organization:** Moved 14 root-level test files to `tests/` directory

#### Documentation Updates
- **README.md:** Complete rewrite for production-ready application
- **CONTRIBUTING.md:** New developer guide with setup and workflow
- **IMPLEMENTATION_STATUS.md:** Updated to reflect v1.0.0 production status
- **CHANGELOG.md:** Comprehensive update with all recent changes
- **File Organization:** All docs now in appropriate subdirectories

#### Code Cleanup
- **Archived Tools:** Moved unused utilities to `tools/archive/`
  - `docx_renderer_multi_slot.py` (superseded)
  - `inspect_docx_headers.py` (utility)
  - `inspect_template.py` (utility)
  - `export_metrics.py` (utility)
  - `metrics_summary.py` (utility)
  - `token_tracker.py` (utility)
  - `render_lesson_plan.py` (utility)
- **Test Consolidation:** All test files now in `tests/` directory
- **Analysis Scripts:** Moved to `tools/archive/`

### Added - Week of 2025-10-01

#### Multi-User Weekly Processing System
- **5-Slot Batch Processing:** Process Monday-Friday lesson plans in single workflow
- **Week Folder Organization:** Automatic file management with `YYYY-MM-DD_WeekOf` structure
- **Multi-User Database:** SQLite with separate workspaces per teacher
- **Real-Time Progress:** SSE streaming for live processing updates
- **File Manager Service:** Automatic organization of inputs/outputs by week

#### Document Processing Pipeline
- **Smart DOCX Parser:** Multi-format support for various teacher file structures
  - Table-based layouts
  - Header-based sections
  - Text-based formats
  - Mixed formats
- **Template Capacity Detection:** Font-size + cell-dimension heuristics for content fitting
- **Multi-Slot Renderer:** Adaptive content distribution across 5 days
- **JSON Merger:** Consolidate 5 individual lessons into weekly plan
- **Template Preservation:** Maintains district DOCX formatting

#### Backend Infrastructure
- **FastAPI REST API:** Complete CRUD operations for lessons and users
- **SSE Progress Streaming:** Real-time updates with backpressure management
- **LLM Service:** OpenAI and Anthropic API integration
- **Mock LLM Service:** Testing without API costs
- **Error Handling:** Comprehensive error recovery and logging
- **CORS Configuration:** Tauri frontend integration

#### Testing & Quality Assurance
- **Unit Tests:** 40+ tests across all modules
- **Integration Tests:** End-to-end workflow validation
- **Mock Testing:** Complete test suite without API dependencies
- **Performance Testing:** Sub-3s processing per slot
- **Test Coverage:** 85%+ on core modules
- **Fixtures:** Valid and invalid test data

#### Documentation
- **User Guides:** Quick start, training, troubleshooting
- **Developer Guides:** Contributing, architecture, testing
- **Deployment Guides:** Production checklist, security review
- **API Documentation:** Auto-generated OpenAPI/Swagger docs
- **Examples:** Sample inputs and outputs

### Added - 2025-10-04

#### Co-Teaching Integration (v1.0)
- **WIDA-Driven Model Selection:** Added `co_teaching/wida_model_rules.json` with simple rules-based selection for 6 Friend & Cook co-teaching models
- **45-Minute Phase Templates:** Added `co_teaching/phase_patterns_45min.json` with detailed phase breakdowns and teacher role specifications
- **Research Foundation:** Integrated Gemini Deep Search findings on co-teaching effectiveness for English Language Learners
- **Equity Focus:** Hardcoded rules to avoid One Teach One Assist/Observe as primary models (equity violations)
- **Prompt Integration:** Added Phase 3 to `prompt_v4.md` for co-teaching model selection based on WIDA proficiency distribution
- **Output Enhancement:** Co-teaching model recommendation now integrated into Tailored Instruction row with 45-minute structure

**Key Features:**
- WIDA band priorities (Levels 1-2, 3-4, 5-6, mixed range)
- Special conditions handling (newcomer %, space constraints, planning time)
- Simple keyword matching for model selection
- Transparent, teacher-friendly rationale

#### Linguistic Misconception Prediction (MVP v1.0)
- **Portuguese→English Interference Patterns:** Added `co_teaching/portuguese_misconceptions.json` with 6 high-frequency patterns
- **Simple Keyword Matching:** Lightweight approach using trigger keywords on lesson objectives/vocabulary
- **Linguistic Notes:** Concise explanations of L1→L2 interference with prevention tips
- **Prompt Integration:** Added Phase 5 to `prompt_v4.md` for linguistic misconception prediction
- **Output Enhancement:** Linguistic notes now appear in Misconceptions row

**Patterns Included (MVP):**
1. Subject pronoun omission (very high frequency)
2. Adjective placement (very high frequency, K-5)
3. Past tense -ed dropping (very high frequency)
4. Preposition: depend ON (very high frequency)
5. False cognate: actual (high frequency, 6-12)
6. False cognate: library (very high frequency, K-5)

**Design Philosophy:** Start simple, grow based on teacher feedback (mirrors co-teaching approach)

#### Documentation Updates
- **Architecture:** Updated `docs/architecture_001.md` with five-phase processing pipeline
- **README:** Updated main `README.md` with new features and version information
- **Co-Teaching README:** Enhanced `co_teaching/README.md` with portuguese_misconceptions.json documentation
- **Integration Plans:** Added `docs/co_teaching_integration_plan.md` (comprehensive research)
- **MVP Documentation:** Added `docs/linguistic_misconceptions_mvp.md` (lightweight approach)
- **Future Planning:** Archived `docs/linguistic_misconceptions_integration_plan_v2_future.md` for potential expansion

### Changed - 2025-10-04

#### Prompt Engine (prompt_v4.md)
- **Processing Pipeline:** Expanded from 3 phases to 5 phases
  - Phase 1: Smart category loading (unchanged)
  - Phase 2: Strategy fine-selection (unchanged)
  - Phase 3: Co-teaching model selection (NEW)
  - Phase 4: Primary-Assessment-First integration (formerly Phase 3)
  - Phase 5: Linguistic misconception prediction (NEW)
- **Misconceptions Row:** Enhanced with linguistic notes and prevention tips
- **Tailored Instruction Row:** Now includes co-teaching model with 45-minute phase plan
- **File Loading:** Added 3 new required files (wida_model_rules.json, phase_patterns_45min.json, portuguese_misconceptions.json)
- **Validation Checklist:** Added checks for co-teaching and linguistic misconception integration

#### Output Structure
- **Tailored Instruction:** Co-teaching model section now appears BEFORE ELL Support (not as separate row)
- **Misconceptions:** Linguistic notes now appear AFTER original content misconception
- **Format:** Maintained Word-compatible markdown table structure

### Design Decisions - 2025-10-04

#### Why Simple Rules-Based Approach?
**Decision:** Use simple JSON rules with keyword matching instead of complex algorithms

**Rationale:**
1. **Consistency:** Mirrors successful co-teaching model selection approach
2. **Speed:** Implementation in days, not weeks
3. **Maintainability:** Easy to update and debug
4. **Transparency:** Teachers can see exactly why recommendations were made
5. **Validation:** Fast feedback loop from real usage

**Alternative Considered:** Comprehensive database with 150+ false cognates, complex prediction algorithm, 10-week implementation
**Why Rejected:** Over-engineering before validating need; delays teacher value; high maintenance burden

#### Why MVP for Linguistic Misconceptions?
**Decision:** Start with 6 high-frequency patterns, grow organically

**Rationale:**
1. **80/20 Rule:** 6 patterns cover ~70-80% of common errors
2. **Fast Validation:** Can test and iterate in weeks, not months
3. **Teacher-Driven Growth:** Add patterns based on real feedback, not assumptions
4. **Low Risk:** Easy to expand if valuable, minimal loss if not

**Growth Path:**
- Month 1: 6 patterns (MVP)
- Month 2-3: Add 4-6 more based on feedback
- Month 6: Expand to 20 patterns if valuable
- Month 12: Consider comprehensive database if demand exists

### Technical Details - 2025-10-04

#### File Structure
```
co_teaching/
├── wida_model_rules.json           # Co-teaching model selection rules
├── phase_patterns_45min.json       # 45-minute phase templates
├── portuguese_misconceptions.json  # Linguistic interference patterns (MVP)
├── co_teaching_models.json         # Model metadata (optional)
├── co_teaching_models.csv          # Reference table
├── co_teaching_strategies.pdf      # Visual guide (757KB)
└── README.md                        # Documentation
```

#### JSON Schema Versions
- **wida_model_rules.json:** v1.0
- **phase_patterns_45min.json:** v1.0
- **portuguese_misconceptions.json:** v1.0 (MVP)

#### Integration Points
- **Prompt:** prompt_v4.md (Phase 3 and Phase 5)
- **Architecture:** docs/architecture_001.md (updated data flow)
- **README:** README.md (updated features and versions)

---

## [2.0.0] - 2025-09-XX (Previous Release)

### Added
- Modular strategy pack architecture (v2.0)
- Intelligent category loading system
- Enhanced schema v1.7 with pedagogical definitions
- Primary-Assessment-First protocol

### Changed
- Migrated from monolithic v1.6 to modular v2.0 strategy pack
- Updated prompt to v4 with smart category pre-selection

---

## Version Numbering

- **Major.Minor.Patch** for system releases
- **vX.Y** for component versions (e.g., Strategy Pack v2.0, Schema v1.7)
- **MVP vX.Y** for minimum viable product releases

---

## Future Roadmap

### Co-Teaching Enhancements (Potential)
- Add model-specific strategy compatibility scores
- Expand to 20+ phase pattern variations
- Add transition time cost calculations
- Integrate teacher capacity assessments

### Linguistic Misconceptions Expansion (Potential)
- Grow to 20 patterns based on teacher feedback
- Add grade-level filtering
- Add phonological pattern detection
- Consider comprehensive database if MVP proves valuable

### Assessment Integration (Planned)
- Enhanced assessment overlay templates
- Model-specific assessment recommendations
- Linguistic growth rubrics

---

**Note:** This changelog follows [Keep a Changelog](https://keepachangelog.com/) principles.

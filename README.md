# Bilingual Weekly Plan Builder

A production-ready desktop application for transforming teacher lesson plans into WIDA-enhanced bilingual weekly plans with research-backed strategies and proficiency-responsive adaptations for Portuguese-English multilingual learners.

## Quick Start

### For End Users
1. **Launch the application** - Double-click the desktop icon
2. **Upload your lesson plan** - Drag & drop your weekly DOCX file
3. **Review & generate** - System automatically processes all 5 days
4. **Download** - Get your enhanced bilingual weekly plan in DOCX format

See **[Quick Start Guide](docs/guides/QUICK_START_GUIDE.md)** for detailed instructions.

### For Developers
```bash
# Backend
cd backend
python -m uvicorn api:app --reload

# Frontend
cd frontend
npm run tauri dev
```

See **[Developer Guide](docs/CONTRIBUTING.md)** for setup instructions.

## System Architecture

```
Bilingual Weekly Plan Builder/
├── frontend/              # Tauri + React/TypeScript UI (PC version, references unified frontend)
├── lesson-plan-browser/
│   └── frontend/          # Unified frontend (PC + Tablet, platform-aware)
├── shared/                # Shared modules (lesson-api, lesson-browser, lesson-mode)
├── backend/               # Python FastAPI service
│   ├── api.py            # REST API endpoints + SSE
│   ├── database.py       # SQLite multi-user storage
│   ├── llm_service.py    # OpenAI/Anthropic integration
│   └── file_manager.py   # Week folder organization
├── tools/                 # Core processing pipeline
│   ├── docx_parser.py    # Multi-format DOCX parsing
│   ├── docx_renderer.py  # Template-based DOCX generation
│   ├── batch_processor.py # 5-slot weekly processing
│   └── json_merger.py    # Weekly plan consolidation
├── templates/             # Jinja2 rendering templates
├── strategies_pack_v2/    # 33 bilingual strategies (6 categories)
├── wida/                  # WIDA 2020 framework
├── co_teaching/           # 6 Friend & Cook models
└── schemas/               # JSON validation schemas
```

## Key Features

### Multi-User Weekly Processing
- **5-slot batch processing** - Process Monday-Friday in one workflow
- **Week folder organization** - Automatic file management by week
- **Multi-user support** - Separate workspaces per teacher
- **Progress tracking** - Real-time SSE updates during processing
- **Template preservation** - Maintains district DOCX formatting

### WIDA-Enhanced Transformations
- **Proficiency-responsive scaffolding** - Differentiated supports for Levels 1-6
- **33 research-backed strategies** - Modular strategy pack across 6 categories
- **Co-teaching model integration** - 6 Friend & Cook models with role specifications
- **Linguistic misconception prevention** - Portuguese→English interference patterns
- **Primary-Assessment-First protocol** - Preserves original assessments with WIDA overlay

### Intelligent Processing
- **Smart DOCX parsing** - Handles multiple teacher formats (tables, headers, text)
- **Template capacity detection** - Font-size + cell-dimension heuristics
- **Multi-slot rendering** - Adaptive content fitting across 5 days
- **JSON validation** - Schema-based quality assurance
- **Error recovery** - Automatic retry logic with exponential backoff

### Privacy & Security
- **Local-first architecture** - All processing on localhost (SQLite) or cloud (Supabase)
- **PII scrubbing** - Automatic removal of sensitive data before LLM calls
- **Secure API key storage** - OS keychain integration
- **Flexible data storage** - Choose SQLite for local-only or Supabase for cloud sync
- **Cross-platform sync** - Supabase enables data access across devices and Android apps

## Documentation

### User Guides
- **[Quick Start Guide](docs/guides/QUICK_START_GUIDE.md)** - Get started in 5 minutes
- **[User Training Guide](docs/training/USER_TRAINING_GUIDE.md)** - Complete user manual
- **[Troubleshooting Guide](docs/guides/TROUBLESHOOTING_QUICK_REFERENCE.md)** - Common issues and solutions

### Developer Documentation
- **[Architecture Overview](docs/ARCHITECTURE_MULTI_USER.md)** - System design and data flow
- **[Unified Frontend Implementation Guide](docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md)** - Guide for unified PC/tablet frontend (platform detection)
- **[Implementation Status](docs/IMPLEMENTATION_STATUS.md)** - Current feature status
- **[Testing Guide](docs/guides/TESTING_GUIDE.md)** - Test suite and procedures
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development setup and guidelines
- **[Tech Stack ADR](docs/decisions/ADR-001-tech-stack.md)** - Technology decisions
- **[Supabase Setup Guide](docs/supabase_setup.md)** - Cloud database configuration and migration

### Deployment
- **[Deployment Checklist](docs/deployment/DEPLOYMENT_CHECKLIST.md)** - Production deployment steps
- **[Production Package](docs/deployment/PRODUCTION_DEPLOYMENT_PACKAGE.md)** - Release preparation
- **[Security Review](docs/security/SECURITY_REVIEW.md)** - Security best practices

### Reference
- **[Strategy Dictionary](docs/bilingual_strategies_dictionary.md)** - All 33 bilingual strategies
- **[Co-Teaching Models](co_teaching/README.md)** - Friend & Cook model reference
- **[WIDA Framework](wida/README.md)** - WIDA 2020 integration details
- **[Examples](docs/examples/)** - Sample inputs and outputs

### Lesson Step Schema Alignment (Nov 2025)
- Run `python backend/migrations/upgrade_lesson_steps_table.py` after pulling latest changes to migrate local SQLite databases.
- Cloud deployments must manually run `sql/create_lesson_steps_table_supabase.sql` in the Supabase SQL editor to apply the same schema.
- Lesson-step regeneration now uses the `delete_lesson_steps(plan_id, day_of_week, slot_number)` API to replace steps safely; new integration tests cover the generate + fetch round trip.

### Supabase Data & RLS Sync
1. **Apply service-role friendly RLS policies** – run `sql/update_rls_service_role_support.sql` in each Supabase project (Wilson & Daniela) so the backend’s service role key can read/write while end-users remain scoped to their own rows.
2. **Seed users into Supabase** – run `python tools/sync_users_to_supabase.py` (or `--project project1/project2`) to upsert the existing SQLite users into Supabase. This keeps the `/api/users` endpoint in sync across environments.

### Multi-Period Lesson Linking (Nov 2025)
New schedule + slot metadata make it possible to explicitly link any periods—even if they are separated by Lunch or other classes—to the same lesson-plan slot.

1. **Run the migrations**
   - SQLite: `python backend/migrations/add_plan_slot_group_id_to_schedules.py` (adds `plan_slot_group_id` to `schedules`) and `python migrate_db.py` (adds `plan_group_label` to `class_slots`).
   - Supabase: execute `sql/add_plan_slot_group_id_to_schedules.sql` and `sql/add_plan_group_label_to_class_slots.sql` in each project.
2. **Label slots** – In **Schedule » Slot Configurator**, every slot now has a “Linked Lesson Group Label”. Use the suggested subject/grade label or enter your own (e.g., “ELA Block A”). The designer shows how many schedule periods currently use that label.
3. **Link periods in the schedule grid** – When editing a cell in **Schedule Input**, assign the same group label (datalist includes both existing schedule labels and slot labels). Labels stay editable even if the two periods are not consecutive.
4. **Validation & visibility**
   - The grid highlights conflicts if two periods in the same group have different subjects/grades/homerooms.
   - Week View cards and the Lesson Detail pane now show a “Group: …” badge so you can confirm which lesson slot a period belongs to.
   - Lesson generation relies on `plan_slot_group_id`, so once a single period is aligned with a plan slot, every other period in that group automatically reuses the same plan content.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Tauri + React + TypeScript | Desktop UI with native performance |
| **Backend** | Python FastAPI | REST API + SSE streaming |
| **Storage** | SQLite / Supabase PostgreSQL | Multi-user data persistence, cloud sync support |
| **Document Processing** | python-docx + docxcompose | DOCX parsing and generation |
| **LLM Integration** | OpenAI/Anthropic APIs | AI-powered transformations |
| **Templating** | Jinja2 | Markdown rendering |
| **Deployment** | PyInstaller | Single-file executable |

## Performance

- **Core processing**: p95 < 3s per slot
- **Weekly workflow**: < 10 minutes for 5 days
- **Parallel processing**: Simultaneous slot parsing
- **Cached JSON**: Reuse validated outputs

## Version Information

- **Application**: v1.0.0 (Production Ready)
- **Strategy Pack**: v2.0 (33 strategies, 6 categories)
- **WIDA Framework**: 2020 Edition
- **Co-Teaching Models**: v1.0 (6 Friend & Cook models)
- **Prompt Engine**: v4 (with linguistic misconceptions)

## System Requirements

- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for application + data
- **Network**: Internet connection for LLM API calls

## License & Context

This system is designed for bilingual education specialists working with Portuguese-English multilingual learners in K-12 settings. All strategies are research-backed and aligned with WIDA 2020 standards.

**Copyright © 2025** - All rights reserved.

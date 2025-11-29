# Documentation

Comprehensive documentation for the Bilingual Lesson Plan Transformation System.

## Core Documentation

### **[Architecture](architecture_001.md)**
Complete system architecture including:
- Data layer (JSON files and modular strategy pack)
- Documentation layer (Markdown files)
- Data flow architecture (3-phase processing pipeline)
- File relationships and dependencies
- Version control and evolution
- Quality assurance framework

### **[Bilingual Strategies Dictionary](bilingual_strategies_dictionary.md)**
Human-readable reference guide for all 33 research-backed bilingual teaching strategies:
- Detailed descriptions and core principles
- Implementation steps and look-fors
- Skill weights and delivery modes
- L1 integration modes
- WIDA alignments
- Research foundations

### **[App Overview](app_overview.md)**
Application architecture and implementation details:
- Tauri + FastAPI technology stack
- Document processing pipeline
- User interface design
- API integration
- Deployment strategy

## Examples

### **[examples/](examples/)**
Sample lesson plans and transformation outputs:
- **Sample_lesson_plan.md** - Example primary teacher lesson plan
- **Sample_Lesson_Transformation_WIDA.md** - WIDA-enhanced bilingual transformation output

## Architecture Decision Records (ADRs)

### **[decisions/](decisions/)**
Technology and design decisions:
- **ADR-001-tech-stack.md** - Technology stack selection rationale

## Quick Reference

### File Locations
- **Primary Prompt:** `../prompt_v4.md`
- **Strategy Pack:** `../strategies_pack_v2/`
- **WIDA Files:** `../wida/`

### Key Concepts

**Schema Version:** v1.7_enhanced
- Enhanced pedagogical definitions with look_fors and non_examples
- Comprehensive WIDA alignment fields
- Skill weights and delivery modes
- L1 integration patterns

**Strategy Pack v2.0:**
- Modular architecture with 6 category files
- Intelligent category loading (2-4 categories per lesson)
- 33 total strategies across core and specialized categories

**Prompt v4 Features:**
- Two-phase strategy selection
- Primary-Assessment-First protocol
- Tri-objective generation system
- Word-compatible markdown table output
- Grade-level variable system

## Contributing

When adding documentation:
1. Follow existing markdown formatting conventions
2. Update this README with new document links
3. Cross-reference related documents
4. Include practical examples where applicable
5. Update architecture document if system changes

## Maintenance

Documentation should be updated when:
- New strategies are added to the pack
- WIDA framework is updated
- Prompt engine receives major enhancements
- Application architecture changes
- New features are implemented

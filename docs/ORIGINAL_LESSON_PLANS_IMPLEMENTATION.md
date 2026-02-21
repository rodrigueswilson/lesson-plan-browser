# Original Lesson Plans Implementation Guide

## Overview

This document describes how to implement the new workflow that:
1. Extracts and stores original lesson plan content in the database
2. Generates a combined DOCX of all original content
3. Enables parallel LLM processing

## Architecture Benefits

### Current Workflow (Sequential)
```
Slot 1: Open file → Extract → LLM (2 min) → Done
Slot 2: Open file → Extract → LLM (2 min) → Done
Slot 3: Open file → Extract → LLM (2 min) → Done
Slot 4: Open file → Extract → LLM (2 min) → Done
Total: ~8 minutes
```

### New Workflow (Parallel)
```
Phase 1 (Sequential - File Operations):
  Slot 1: Open file → Extract → Store in DB → Close
  Slot 2: Open file → Extract → Store in DB → Close
  Slot 3: Open file → Extract → Store in DB → Close
  Slot 4: Open file → Extract → Store in DB → Close
  Time: ~30 seconds

Phase 2 (Optional):
  Generate combined original DOCX from database
  Time: ~10 seconds

Phase 3 (Parallel - LLM Processing):
  All slots: Read from DB → LLM API calls (parallel)
  Time: ~2 minutes (all running simultaneously)
  
Total: ~2.5 minutes (vs 8 minutes)
```

## Implementation Steps

### Step 1: Run Migration

**SQLite:**
```bash
python backend/migrations/create_original_lesson_plans_table.py
```

**Supabase:**
Run the SQL from `sql/create_original_lesson_plans_table_supabase.sql` in Supabase SQL editor.

### Step 2: Modify Batch Processor

Add new method to extract and store original content:

```python
async def _extract_and_store_original_content(
    self,
    slot: Dict[str, Any],
    week_of: str,
    user_id: str,
    week_folder_path: Optional[str] = None,
    user_base_path: Optional[str] = None,
) -> str:
    """
    Extract content from primary teacher file and store in database.
    
    Returns:
        original_plan_id: ID of the stored original lesson plan
    """
    # 1. Resolve primary file
    primary_file = self._resolve_primary_file(...)
    
    # 2. Open and extract content
    parser = await self._open_docx_with_retry(...)
    content = parser.extract_subject_content(...)
    
    # 3. Store in database
    original_plan = OriginalLessonPlan(
        id=f"original_{user_id}_{week_of}_{slot['slot_number']}",
        user_id=user_id,
        week_of=week_of,
        slot_number=slot['slot_number'],
        subject=slot['subject'],
        grade=slot['grade'],
        homeroom=slot.get('homeroom'),
        source_file_path=primary_file,
        source_file_name=Path(primary_file).name,
        primary_teacher_name=slot.get('primary_teacher_name'),
        content_json=content,
        full_text=content.get('full_text', ''),
        available_days=content.get('available_days', []),
        has_no_school=parser.is_no_school_day(),
        status='extracted'
    )
    
    db.create_original_lesson_plan(original_plan)
    return original_plan.id
```

### Step 3: Generate Combined Original DOCX

```python
def generate_combined_original_docx(
    self,
    user_id: str,
    week_of: str,
    output_path: str
) -> str:
    """
    Generate a combined DOCX showing all original lesson plans.
    
    Structure:
    - Page 1: Slot 1 (ELA/SS) - Original content
    - Page 2: Slot 2 (Science) - Original content
    - Page 3: Slot 3 (Math) - Original content
    - etc.
    """
    # Query all original plans for this week
    original_plans = db.get_original_lesson_plans(user_id, week_of)
    
    # Create combined DOCX
    from docx import Document
    from docxcompose.composer import Composer
    
    master = Document()
    composer = Composer(master)
    
    for plan in sorted(original_plans, key=lambda x: x.slot_number):
        # Create DOCX for this slot's original content
        slot_doc = self._render_original_content(plan)
        composer.append(slot_doc)
    
    composer.save(output_path)
    return output_path
```

### Step 4: Parallel LLM Processing

```python
async def _process_slots_parallel(
    self,
    user_id: str,
    week_of: str,
    provider: str,
    plan_id: str,
) -> List[Dict[str, Any]]:
    """
    Process all slots in parallel using stored original content.
    """
    # Get all original plans from database
    original_plans = db.get_original_lesson_plans(user_id, week_of)
    
    # Create tasks for parallel processing
    tasks = []
    for original_plan in original_plans:
        task = self._process_slot_from_db(
            original_plan=original_plan,
            week_of=week_of,
            provider=provider,
            plan_id=plan_id,
        )
        tasks.append(task)
    
    # Process all in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results
    lessons = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Slot {i+1} failed: {result}")
        else:
            lessons.append(result)
    
    return lessons
```

## Database Methods Needed

Add to `backend/database.py`:

```python
def create_original_lesson_plan(self, plan: OriginalLessonPlan) -> str:
    """Create an original lesson plan record."""
    
def get_original_lesson_plans(self, user_id: str, week_of: str) -> List[OriginalLessonPlan]:
    """Get all original lesson plans for a week."""
    
def update_original_lesson_plan_status(self, plan_id: str, status: str):
    """Update the status of an original lesson plan."""
```

## Benefits Summary

1. **4x Faster**: Parallel processing reduces time from 8 min to ~2 min
2. **No File Locking**: Files read once, stored in DB
3. **Combined View**: Generate DOCX of all originals for review
4. **Versioning**: Track changes to original content
5. **Audit Trail**: See exactly what was used for LLM transformation
6. **Better Error Handling**: Can retry LLM without re-reading files

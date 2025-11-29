# Quick Start: Multi-User System

## Setup (One-Time)

### 1. Start the API Server

```bash
cd d:\LP
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### 2. Create Users

```python
from backend.database import get_db

db = get_db()

# Create first user (you)
user1_id = db.create_user("Your Name", "your.email@school.edu")

# Create second user (wife)
user2_id = db.create_user("Wife's Name", "wife.email@school.edu")

print(f"User 1 ID: {user1_id}")
print(f"User 2 ID: {user2_id}")
```

### 3. Configure Class Slots

```python
# For User 1 - Configure 6 class slots
slots_config = [
    {"slot": 1, "subject": "Math", "grade": "6", "homeroom": "6A", "file": "input/primary_math.docx"},
    {"slot": 2, "subject": "Science", "grade": "6", "homeroom": "6B", "file": "input/primary_science.docx"},
    {"slot": 3, "subject": "ELA", "grade": "6", "homeroom": "6C", "file": "input/primary_ela.docx"},
    {"slot": 4, "subject": "Social Studies", "grade": "6", "homeroom": "6A", "file": "input/primary_ss.docx"},
    {"slot": 5, "subject": "Math", "grade": "7", "homeroom": "7A", "file": "input/primary_math_7.docx"},
    {"slot": 6, "subject": "Science", "grade": "7", "homeroom": "7B", "file": "input/primary_science_7.docx"},
]

for config in slots_config:
    db.create_class_slot(
        user_id=user1_id,
        slot_number=config["slot"],
        subject=config["subject"],
        grade=config["grade"],
        homeroom=config["homeroom"],
        primary_teacher_file=config["file"]
    )

print("✅ Configured 6 class slots for User 1")
```

---

## Weekly Workflow

### Option 1: Python Script

```python
import asyncio
from tools.batch_processor import process_batch

async def generate_weekly_plan():
    # Process all 6 slots for the week
    result = await process_batch(
        user_id="your-user-id-here",
        week_of="10/07-10/11",
        provider="openai"  # or "anthropic"
    )
    
    if result['success']:
        print(f"✅ Success!")
        print(f"Output: {result['output_file']}")
        print(f"Processed: {result['processed_slots']} slots")
        print(f"Time: {result['total_time_ms']/1000:.1f}s")
    else:
        print(f"❌ Failed!")
        print(f"Errors: {result['errors']}")

# Run it
asyncio.run(generate_weekly_plan())
```

### Option 2: API Call

```bash
curl -X POST http://localhost:8000/api/process-week \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id-here",
    "week_of": "10/07-10/11",
    "provider": "openai"
  }'
```

### Option 3: Simple Script

Create `generate_plan.py`:

```python
import asyncio
import sys
from tools.batch_processor import process_batch

async def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else "your-default-user-id"
    week_of = sys.argv[2] if len(sys.argv) > 2 else "10/07-10/11"
    
    print(f"Processing week {week_of} for user {user_id[:8]}...")
    
    result = await process_batch(user_id, week_of, "openai")
    
    if result['success']:
        print(f"✅ Generated: {result['output_file']}")
    else:
        print(f"❌ Failed: {result['errors']}")

asyncio.run(main())
```

Run it:
```bash
python generate_plan.py <user_id> "10/07-10/11"
```

---

## Managing Slots

### View Current Slots

```python
from backend.database import get_db

db = get_db()
slots = db.get_user_slots("your-user-id")

for slot in slots:
    print(f"Slot {slot['slot_number']}: {slot['subject']} - Grade {slot['grade']} - Room {slot['homeroom']}")
```

### Update a Slot

```python
# Change homeroom for slot
db.update_class_slot(
    slot_id="slot-id-here",
    homeroom="6D"
)

# Change primary teacher file
db.update_class_slot(
    slot_id="slot-id-here",
    primary_teacher_file="input/new_primary_math.docx"
)
```

### Delete a Slot

```python
db.delete_class_slot("slot-id-here")
```

---

## View History

### Get All Plans for a User

```python
from backend.database import get_db

db = get_db()
plans = db.get_user_plans("your-user-id", limit=10)

for plan in plans:
    print(f"Week: {plan['week_of']}")
    print(f"Status: {plan['status']}")
    print(f"File: {plan['output_file']}")
    print(f"Generated: {plan['generated_at']}")
    print("---")
```

---

## File Organization

### Input Files (Primary Teacher Plans)

Place primary teacher DOCX files in `input/` folder:
```
input/
  ├── primary_math.docx
  ├── primary_science.docx
  ├── primary_ela.docx
  ├── primary_ss.docx
  ├── primary_math_7.docx
  └── primary_science_7.docx
```

### Output Files (Generated Plans)

Generated files appear in `output/` folder:
```
output/
  └── Your_Name_Lesson plan_W06_10-07-10-11.docx
```

### Database

SQLite database stores all configurations:
```
data/
  └── lesson_planner.db
```

---

## Troubleshooting

### Issue: "User not found"

**Solution:** Get user ID first:
```python
from backend.database import get_db
db = get_db()
users = db.list_users()
for user in users:
    print(f"{user['name']}: {user['id']}")
```

### Issue: "Primary teacher file not found"

**Solution:** Verify file path:
```python
from pathlib import Path
file_path = Path("input/primary_math.docx")
print(f"Exists: {file_path.exists()}")
```

### Issue: "Slot processing failed"

**Solution:** Check individual slot:
```python
from tools.docx_parser import DOCXParser

parser = DOCXParser("input/primary_math.docx")
content = parser.extract_subject_content("Math")
print(f"Extracted: {len(content['full_text'])} characters")
```

### Issue: "LLM transformation failed"

**Solution:** Check API key:
```python
import os
print(f"OpenAI Key: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
print(f"Anthropic Key: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
```

---

## Tips & Best Practices

### 1. Backup Database Regularly

```bash
# Copy database file
copy data\lesson_planner.db data\lesson_planner_backup.db
```

### 2. Test with Mock LLM First

```python
from backend.mock_llm_service import get_mock_llm_service
from tools.batch_processor import BatchProcessor

llm_service = get_mock_llm_service()
processor = BatchProcessor(llm_service)

result = await processor.process_user_week(user_id, week_of, "mock")
```

### 3. Process One Slot at a Time (for testing)

```python
from tools.docx_parser import DOCXParser
from backend.llm_service import get_llm_service

# Parse
parser = DOCXParser("input/primary_math.docx")
content = parser.extract_subject_content("Math")

# Transform
llm = get_llm_service()
success, lesson_json, error = llm.transform_lesson(
    primary_content=content['full_text'],
    grade="6",
    subject="Math",
    week_of="10/07-10/11"
)

# Render
from tools.docx_renderer import DOCXRenderer
renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")
renderer.render(lesson_json, "output/test_math.docx")
```

### 4. Verify Output Before Submitting

1. Open generated DOCX
2. Check all 6 classes are included
3. Verify signature box is present
4. Confirm filename format is correct

---

## Advanced Usage

### Parallel Processing (Future)

```python
import asyncio

async def process_multiple_users():
    user_ids = ["user1-id", "user2-id"]
    week_of = "10/07-10/11"
    
    tasks = [
        process_batch(user_id, week_of, "openai")
        for user_id in user_ids
    ]
    
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"User {i+1}: {result['output_file']}")

asyncio.run(process_multiple_users())
```

### Custom Error Handling

```python
async def safe_process():
    try:
        result = await process_batch(user_id, week_of, "openai")
        
        if result['success']:
            # Send email notification
            # Update tracking spreadsheet
            # Archive to shared drive
            pass
        else:
            # Log errors
            # Notify admin
            # Retry failed slots
            pass
            
    except Exception as e:
        print(f"Critical error: {e}")
        # Fallback to manual process
```

---

## Next Steps

1. ✅ Configure your class slots
2. ✅ Place primary teacher files in `input/`
3. ✅ Run batch processor for the week
4. ✅ Review generated DOCX
5. ✅ Submit to administration

**Questions?** See `docs/USER_PROFILE_GUIDE.md` for detailed documentation.

# User Profile System Guide

## Overview

The User Profile System enables multi-user support with persistent storage of user configurations, class slots, and weekly plan history. Built on SQLite, it provides a robust foundation for managing multiple bilingual teachers and their class schedules.

## Architecture

### Database Schema

**Users Table:**
- `id` (TEXT, PRIMARY KEY) - UUID
- `name` (TEXT) - User's full name
- `email` (TEXT) - User's email address
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

**Class Slots Table:**
- `id` (TEXT, PRIMARY KEY) - UUID
- `user_id` (TEXT, FOREIGN KEY) - References users(id)
- `slot_number` (INTEGER) - Slot number (1-6)
- `subject` (TEXT) - Subject name
- `grade` (TEXT) - Grade level
- `homeroom` (TEXT) - Homeroom/class identifier
- `proficiency_levels` (TEXT) - JSON string of proficiency levels
- `primary_teacher_file` (TEXT) - Path to primary teacher's DOCX file
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp

**Weekly Plans Table:**
- `id` (TEXT, PRIMARY KEY) - UUID
- `user_id` (TEXT, FOREIGN KEY) - References users(id)
- `week_of` (TEXT) - Week date range (MM/DD-MM/DD)
- `generated_at` (TIMESTAMP) - Generation timestamp
- `output_file` (TEXT) - Path to generated DOCX file
- `status` (TEXT) - Plan status (pending, processing, completed, failed)
- `error_message` (TEXT) - Error message if failed

## API Endpoints

### User Management

#### Create User
```http
POST /api/users
Content-Type: application/json

{
  "name": "Maria Garcia",
  "email": "maria@school.edu"
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Maria Garcia",
  "email": "maria@school.edu",
  "created_at": "2025-10-05T11:00:00",
  "updated_at": "2025-10-05T11:00:00"
}
```

#### List Users
```http
GET /api/users
```

#### Get User
```http
GET /api/users/{user_id}
```

### Class Slot Management

#### Create Class Slot
```http
POST /api/users/{user_id}/slots
Content-Type: application/json

{
  "slot_number": 1,
  "subject": "Math",
  "grade": "6",
  "homeroom": "6A",
  "proficiency_levels": "{\"levels\": [\"1\", \"2\", \"3\"]}",
  "primary_teacher_file": "input/primary_math.docx"
}
```

#### Get User's Slots
```http
GET /api/users/{user_id}/slots
```

#### Update Slot
```http
PUT /api/slots/{slot_id}
Content-Type: application/json

{
  "subject": "Science",
  "grade": "7"
}
```

#### Delete Slot
```http
DELETE /api/slots/{slot_id}
```

### Weekly Plans

#### Get User's Plans
```http
GET /api/users/{user_id}/plans?limit=50
```

#### Process Week (Batch)
```http
POST /api/process-week
Content-Type: application/json

{
  "user_id": "uuid-here",
  "week_of": "10/07-10/11",
  "provider": "openai"
}
```

**Response:**
```json
{
  "success": true,
  "plan_id": "uuid-here",
  "output_file": "output/Maria_Garcia_Lesson plan_W06_10-07-10-11.docx",
  "processed_slots": 6,
  "failed_slots": 0,
  "total_time_ms": 15000,
  "errors": null
}
```

## Python Usage

### Database Operations

```python
from backend.database import get_db

# Get database instance
db = get_db()

# Create user
user_id = db.create_user("Maria Garcia", "maria@school.edu")

# Create class slot
slot_id = db.create_class_slot(
    user_id=user_id,
    slot_number=1,
    subject="Math",
    grade="6",
    homeroom="6A",
    proficiency_levels='{"levels": ["1", "2", "3"]}',
    primary_teacher_file="input/primary_math.docx"
)

# Get user's slots
slots = db.get_user_slots(user_id)

# Update slot
db.update_class_slot(slot_id, homeroom="6B")

# Create weekly plan
plan_id = db.create_weekly_plan(user_id, "10/07-10/11")

# Update plan status
db.update_weekly_plan(plan_id, status="completed", output_file="output/plan.docx")
```

### Batch Processing

```python
from tools.batch_processor import process_batch

# Process all slots for a user's week
result = await process_batch(
    user_id="uuid-here",
    week_of="10/07-10/11",
    provider="openai"
)

if result['success']:
    print(f"Generated: {result['output_file']}")
else:
    print(f"Errors: {result['errors']}")
```

## Workflow

### Initial Setup

1. **Create User Profile**
   - Add user with name and email
   - System generates unique user ID

2. **Configure Class Slots**
   - Add up to 6 class slots per user
   - Each slot includes:
     - Slot number (1-6)
     - Subject and grade
     - Homeroom identifier
     - Proficiency levels (JSON)
     - Path to primary teacher's DOCX file

3. **Save Configuration**
   - All settings persist in SQLite database
   - Reusable week-to-week

### Weekly Processing

1. **Trigger Batch Process**
   - Provide user ID and week date range
   - System processes all configured slots

2. **For Each Slot:**
   - Extract content from primary teacher's DOCX
   - Transform to bilingual lesson plan via LLM
   - Validate against schema
   - Render to DOCX

3. **Combine Results**
   - Merge all slots into single DOCX
   - Add signature box with date
   - Save with proper filename format

4. **Track History**
   - Record weekly plan in database
   - Store output file path
   - Track status and errors

## Multi-User Support

### Scenario: Two Teachers

**Maria Garcia (6th Grade ESL):**
- Slot 1: Math, Grade 6, Room 6A
- Slot 2: Science, Grade 6, Room 6B
- Slot 3: ELA, Grade 6, Room 6C
- Slot 4: Social Studies, Grade 6, Room 6A
- Slot 5: Math, Grade 6, Room 6D
- Slot 6: Science, Grade 6, Room 6E

**John Smith (7th Grade ESL):**
- Slot 1: Math, Grade 7, Room 7A
- Slot 2: Science, Grade 7, Room 7B
- Slot 3: ELA, Grade 7, Room 7C
- Slot 4: Social Studies, Grade 7, Room 7A

Each teacher can:
- Process their own weekly plans independently
- Maintain separate configurations
- Access their own plan history
- Update their slots as needed

## File Naming Convention

Output files follow this format:
```
{Name}_Lesson plan_W{WeekNum}_{DateRange}.docx
```

Examples:
- `Maria_Garcia_Lesson plan_W06_10-07-10-11.docx`
- `John_Smith_Lesson plan_W06_10-07-10-11.docx`

## Data Persistence

### Database Location
- Default: `data/lesson_planner.db`
- Configurable via Database constructor

### Backup Recommendations
1. Regular SQLite database backups
2. Export user configurations to JSON
3. Archive generated DOCX files

### Data Retention
- Users: Permanent until manually deleted
- Class Slots: Permanent until manually deleted
- Weekly Plans: Configurable retention (default: all)

## Error Handling

### Slot Processing Errors
- Individual slot failures don't stop batch
- Errors recorded in weekly plan
- Partial results still combined

### Database Errors
- Transactions ensure consistency
- Foreign key constraints prevent orphaned data
- Cascade deletes clean up related records

## Security Considerations

1. **API Keys**: Stored in OS keychain (not in database)
2. **File Paths**: Validated before use
3. **User Data**: No PII in generated content
4. **Database**: Local SQLite (no network exposure)

## Testing

Run user profile tests:
```bash
pytest tests/test_user_profiles.py -v
```

Run integration test:
```bash
python test_user_workflow.py
```

## Troubleshooting

### Database Locked
- Close other connections
- Check for long-running transactions

### Slot Not Found
- Verify user_id and slot_id are correct
- Check if slot was deleted

### Batch Processing Fails
- Verify all primary teacher files exist
- Check LLM service is available
- Review error messages in weekly plan

## Future Enhancements

- [ ] User authentication/authorization
- [ ] Role-based access control
- [ ] Shared slot templates
- [ ] Bulk import/export
- [ ] Analytics dashboard
- [ ] Email notifications

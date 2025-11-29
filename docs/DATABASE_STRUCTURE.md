# Database Structure Guide

## Overview

This project uses a **SQLite database** to store information about users, their class schedules, lesson plans, and performance metrics. SQLite is a lightweight database that stores data in a single file on your computer.

## Database Location

The database file is located at: `data/lesson_planner.db` (or `data/lesson_plans.db` depending on configuration)

## Main Tables

The database has 4 main tables that work together:

### 1. `users` Table
**Purpose**: Stores information about teachers/users of the system

**Columns**:
- `id` - Unique identifier for each user (UUID)
- `name` - Full name (computed from first_name + last_name)
- `first_name` - User's first name
- `last_name` - User's last name
- `email` - Email address (optional)
- `base_path_override` - Custom file path if needed (optional)
- `created_at` - When the user was created
- `updated_at` - When the user was last updated

**Example**: A user might be "Maria Rodriguez" teaching bilingual classes.

---

### 2. `class_slots` Table
**Purpose**: Stores information about each class period/slot that a teacher teaches

**Columns**:
- `id` - Unique identifier for each slot (UUID)
- `user_id` - Links to the `users` table (which teacher owns this slot)
- `slot_number` - Period number (1-6, representing different class periods)
- `subject` - What subject is taught (e.g., "Math", "Science", "ELA")
- `grade` - Grade level (e.g., "6", "7", "8")
- `homeroom` - Homeroom or class identifier (optional)
- `proficiency_levels` - JSON string of student proficiency levels (optional)
- `primary_teacher_file` - Path to the primary teacher's lesson plan file (optional)
- `primary_teacher_name` - Full name of the primary teacher (computed)
- `primary_teacher_first_name` - Primary teacher's first name
- `primary_teacher_last_name` - Primary teacher's last name
- `primary_teacher_file_pattern` - Pattern to match primary teacher files (optional)
- `display_order` - Order for displaying slots (optional)
- `created_at` - When the slot was created
- `updated_at` - When the slot was last updated

**Example**: Maria Rodriguez might have:
- Slot 1: Math, Grade 6, Homeroom 6A
- Slot 2: Science, Grade 7, Homeroom 7B

**Relationship**: Each slot belongs to one user (many slots can belong to one user)

---

### 3. `weekly_plans` Table
**Purpose**: Tracks generated lesson plans for specific weeks

**Columns**:
- `id` - Unique identifier for each plan (UUID)
- `user_id` - Links to the `users` table (which teacher created this plan)
- `week_of` - Week date range (e.g., "09/15-09/19")
- `week_folder_path` - Path to folder containing source files
- `generated_at` - When the plan was generated
- `output_file` - Path to the generated DOCX file
- `status` - Current status: "pending", "processing", "completed", or "failed"
- `error_message` - Error details if generation failed (optional)
- `consolidated` - Whether this is a multi-slot consolidated plan (0 or 1)
- `total_slots` - Number of slots included in this plan
- `processing_time_ms` - How long processing took (milliseconds)
- `total_tokens` - Total LLM tokens used
- `total_cost_usd` - Total cost in USD
- `llm_model` - Which AI model was used

**Example**: A plan for the week of September 15-19, 2025, combining 3 class slots.

**Relationship**: Each plan belongs to one user (many plans can belong to one user)

---

### 4. `performance_metrics` Table
**Purpose**: Tracks detailed performance data for each operation during plan generation

**Columns**:
- `id` - Unique identifier for each metric (UUID)
- `plan_id` - Links to the `weekly_plans` table
- `slot_number` - Which slot this metric is for
- `day_number` - Which day of the week (1-5)
- `operation_type` - Type of operation (e.g., "transform", "generate")
- `started_at` - When the operation started
- `completed_at` - When it finished
- `duration_ms` - How long it took (milliseconds)
- `tokens_input` - Input tokens used
- `tokens_output` - Output tokens generated
- `tokens_total` - Total tokens
- `llm_provider` - AI provider used (e.g., "openai", "anthropic")
- `llm_model` - Specific model used
- `cost_usd` - Cost in USD
- `error_message` - Error if something went wrong (optional)

**Example**: Metrics for transforming Slot 1, Day 3 lesson plan, showing it took 2.3 seconds and used 150 tokens.

**Relationship**: Many metrics can belong to one weekly plan

---

## Relationships Between Tables

Think of the relationships like this:

```
users (1) ──< (many) class_slots
  │
  └──< (many) weekly_plans (1) ──< (many) performance_metrics
```

**Translation**:
- **One user** can have **many class slots** (e.g., Maria teaches 6 different classes)
- **One user** can have **many weekly plans** (e.g., Maria has plans for different weeks)
- **One weekly plan** can have **many performance metrics** (e.g., each operation is tracked separately)

## How It Works Together

1. **Setup**: A teacher (user) creates their profile
2. **Configuration**: The teacher sets up their class slots (which classes they teach)
3. **Generation**: When generating a lesson plan, a weekly_plan record is created
4. **Tracking**: Each step of the generation process creates performance_metrics records

## Key Features

### Foreign Keys
The database uses **foreign keys** to ensure data integrity:
- If you delete a user, all their class slots and weekly plans are automatically deleted (CASCADE)
- This prevents "orphaned" data (slots without owners, etc.)

### Indexes
The database has **indexes** to make queries faster:
- Finding all slots for a user
- Finding all plans for a user
- Finding all metrics for a plan

### Automatic Timestamps
Most tables have `created_at` and `updated_at` fields that are automatically set:
- `created_at` - Set when record is first created
- `updated_at` - Updated whenever the record changes

## Example Data Flow

1. **User Creation**: Maria Rodriguez signs up → `users` table gets a new record
2. **Slot Setup**: Maria configures her 6 class periods → `class_slots` table gets 6 records, all linked to Maria's user_id
3. **Plan Generation**: Maria generates plans for week 9/15-9/19 → `weekly_plans` table gets a new record
4. **Metrics Tracking**: During generation, each operation is tracked → `performance_metrics` table gets multiple records

## Database Initialization

When the application starts, the `Database` class automatically:
1. Creates the database file if it doesn't exist
2. Creates all tables if they don't exist
3. Runs migrations to add new columns if needed
4. Creates indexes for faster queries

## Migrations

The database can be updated over time using **migrations**:
- The `_run_migrations()` method checks for missing columns and adds them
- There's also a separate migration script for adding structured name fields (`add_structured_names.py`)

This allows the database structure to evolve without losing existing data.


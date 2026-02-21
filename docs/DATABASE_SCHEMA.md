# Database Schema Documentation

The project uses **SQLModel** (a wrapper around SQLAlchemy and Pydantic) for database interactions. The schema is primarily defined in `backend/schema.py`.

## Tables Overview

The following tables are defined in the system:

1.  **`users`**: Stores user profile information and preferences.
2.  **`class_slots`**: Configuration for teaching periods/slots.
3.  **`weekly_plans`**: Records of generated weekly lesson plans.
4.  **`schedules`**: User schedule entries linking days, times, and slots.
5.  **`performance_metrics`**: Tracks LLM operation performance and costs.
6.  **`lesson_steps`**: Persists individual steps of a lesson for Lesson Mode.
7.  **`lesson_mode_sessions`**: Maintains the state of active Lesson Mode sessions.

---

## Detailed Table Structures

### 1. `users`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique user identifier. |
| `email` | `str?` | User's email address. |
| `first_name` | `str?` | User's first name. |
| `last_name` | `str?` | User's last name. |
| `name` | `str` | Legacy full name. |
| `base_path_override` | `str?` | Custom base path for file operations. |
| `template_path` | `str?` | Path to the DOCX template. |
| `signature_image_path` | `str?` | Path to the user's signature image. |
| `created_at` | `datetime` | Timestamp of creation. |
| `updated_at` | `datetime` | Timestamp of last update. |

### 2. `class_slots`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique slot configuration identifier. |
| `user_id` | `str` (FK) | Reference to `users.id` (Indexed). |
| `slot_number` | `int` | Sequential slot number (1-10). |
| `subject` | `str` | Name of the subject. |
| `grade` | `str` | Grade level. |
| `homeroom` | `str?` | Homeroom identifier. |
| `plan_group_label` | `str?` | Label for grouping plans. |
| `proficiency_levels` | `str?` | WIDA proficiency levels description. |
| `primary_teacher_file` | `str?` | Path to the source file from the primary teacher. |
| `primary_teacher_name` | `str?` | Name of the primary teacher. |
| `primary_teacher_first_name` | `str?` | First name of the primary teacher. |
| `primary_teacher_last_name` | `str?` | Last name of the primary teacher. |
| `primary_teacher_file_pattern`| `str?` | Regex pattern for matching source files. |
| `display_order` | `int` | Sort order for display (default: 0). |
| `created_at` | `datetime` | Timestamp of creation. |
| `updated_at` | `datetime` | Timestamp of last update. |

### 3. `weekly_plans`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique plan identifier. |
| `user_id` | `str` (FK) | Reference to `users.id` (Indexed). |
| `week_of` | `str` | Range string (e.g., "MM/DD-MM/DD"). |
| `status` | `str` | Status of generation ("pending", "completed", "failed"). |
| `output_file` | `str?` | Path to the generated DOCX file. |
| `week_folder_path` | `str?` | Directory containing week's assets. |
| `consolidated` | `int` | Whether results are consolidated (0 or 1). |
| `total_slots` | `int` | Number of slots in the plan. |
| `generated_at` | `datetime` | Timestamp of generation. |
| `processing_time_ms` | `float?` | Total LLM processing time. |
| `total_tokens` | `int?` | Total tokens used. |
| `total_cost_usd` | `float?` | Total cost of generation. |
| `llm_model` | `str?` | Name of the LLM model used. |
| `error_message` | `str?` | Details if generation failed. |
| `lesson_json` | `JSON?` | Full lesson plan data as JSON. |

### 4. `schedules`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique schedule entry identifier. |
| `user_id` | `str` (FK) | Reference to `users.id` (Indexed). |
| `day_of_week` | `str` | Day (monday, tuesday, etc.). |
| `slot_number` | `int` | Linked slot number. |
| `start_time` | `str` | Start time (e.g., "08:30 AM"). |
| `end_time` | `str` | End time (e.g., "09:30 AM"). |
| `subject` | `str?` | Subject name (overrides slot subject if present). |
| `grade` | `str?` | Grade level override. |
| `homeroom` | `str?` | Homeroom override. |
| `plan_slot_group_id` | `str?` | links multiple periods to the same lesson plan slot. |
| `is_active` | `bool` | Whether the period is active. |
| `created_at` | `datetime` | Timestamp of creation. |
| `updated_at` | `datetime` | Timestamp of last update. |

### 5. `performance_metrics`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique metric identifier. |
| `plan_id` | `str` (FK) | Reference to `weekly_plans.id` (Indexed). |
| `slot_number` | `int?` | Specific slot number. |
| `day_number` | `int?` | Specific day of school week. |
| `operation_type` | `str` | Type of LLM operation. |
| `started_at` | `datetime` | Operation start time. |
| `completed_at` | `datetime` | Operation completion time. |
| `duration_ms` | `float` | Duration in milliseconds. |
| `tokens_input` | `int?` | Input token count. |
| `tokens_output` | `int?` | Output token count. |
| `tokens_total` | `int?` | Sum of input and output tokens. |
| `llm_provider` | `str?` | Provider (e.g., "openai"). |
| `llm_model` | `str?` | Model name. |
| `cost_usd` | `float?` | Calculated cost of the request. |
| `error_message` | `str?` | Any error occurred during operation. |

### 6. `lesson_steps`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique step identifier. |
| `lesson_plan_id` | `str` (FK) | Reference to `weekly_plans.id` (Indexed). |
| `day_of_week` | `str` | Day of the week. |
| `slot_number` | `int` | Slot number. |
| `step_number` | `int` | Order of step within the lesson. |
| `step_name` | `str` | Name of the step (e.g., "Anticipatory Set"). |
| `duration_minutes` | `int` | Planned duration. |
| `start_time_offset` | `int` | Minutes from lesson start. |
| `content_type` | `str` | Type of content. |
| `display_content` | `str` | Main instruction/content. |
| `hidden_content` | `JSON?` | Hidden or secondary content. |
| `sentence_frames` | `JSON?` | Scaffolding frames. |
| `materials_needed` | `JSON?` | List of items required. |
| `vocabulary_cognates` | `JSON?` | List of key terms and cognates. |
| `created_at` | `datetime` | Timestamp of creation. |
| `updated_at` | `datetime` | Timestamp of last update. |

### 7. `lesson_mode_sessions`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` (PK) | Unique session identifier. |
| `user_id` | `str` (FK) | Reference to `users.id` (Indexed). |
| `lesson_plan_id` | `str` (FK) | Reference to `weekly_plans.id` (Indexed). |
| `schedule_entry_id` | `str?` | Reference to `schedules.id`. |
| `day_of_week` | `str` | Active day. |
| `slot_number` | `int` | Active slot. |
| `current_step_index` | `int` | Index of the current step (starting at 0). |
| `remaining_time` | `int` | Remaining seconds on current timer. |
| `is_running` | `bool` | Whether the timer is running. |
| `is_paused` | `bool` | Whether the session is paused. |
| `is_synced` | `bool` | Sync status. |
| `timer_start_time` | `datetime?`| When the current timer was last started. |
| `paused_at` | `int?` | Elapsed seconds when paused. |
| `adjusted_durations` | `JSON?` | Map of manual duration overrides. |
| `session_start_time` | `datetime` | Overall session start. |
| `last_updated` | `datetime` | Heartbeat timestamp. |
| `ended_at` | `datetime?` | When the session was closed. |

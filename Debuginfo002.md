INFO:     Will watch for changes in these directories: ['D:\\LP']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [7120] using WatchFiles
INFO:     Started server process [13492]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:54905 - "GET /api/users HTTP/1.1" 200 OK
INFO:     127.0.0.1:54904 - "GET /api/users HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54905 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54918 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff HTTP/1.1" 200 OK
INFO:     127.0.0.1:54913 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:54915 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54915 - "GET /api/recent-weeks?user_id=29fa9ed7-3174-4999-86fd-40a542c28cff&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "POST /api/process-week HTTP/1.1" 200 OK

============================================================
PROCESS_USER_WEEK STARTED
User: 29fa9ed7-3174-4999-86fd-40a542c28cff
Week: 10-20-10-24
============================================================

DEBUG: About to call db.get_user()
DEBUG: Got user: Daniela Silva
DEBUG: About to call db.get_user_slots()
DEBUG: Got 5 slots
DEBUG: About to start processing 1 slots
DEBUG: Progress tracker updated - starting

DEBUG: === Starting slot 1/1: ELA/SS ===
DEBUG: Updating progress tracker for slot 1
DEBUG: Progress tracker updated for slot 1
DEBUG: About to call _process_slot for slot 1
DEBUG: _process_slot - Resolving primary file for slot 1
DEBUG: _process_slot - Primary file resolved: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx
DEBUG: _process_slot - Creating DOCXParser
DEBUG: _process_slot - DOCXParser created successfully
DEBUG: _process_slot - Extracting images and hyperlinks
DEBUG: _process_slot - Extracted 0 images, 16 hyperlinks
DEBUG: _process_slot - Checking for No School day
DEBUG: _process_slot - Extracting subject content
DEBUG: _process_slot - Content extracted, length: 5191
DEBUG: _process_slot - No School days detected: ['WEDNESDAY']
DEBUG: _process_slot - Starting performance tracking
DEBUG: _process_slot - Performance tracking started, op_id: 027e4962-6bef-4cc1-abb7-db4d6c29ba25
DEBUG: _process_slot - Calling LLM service transform_lesson
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - LLM transform_lesson returned, success: True
DEBUG: _process_slot - Replacing 1 No School days in output
DEBUG: _process_slot completed for slot 1
DEBUG: Appending lesson for slot 1
DEBUG: Lesson appended for slot 1
DEBUG: === Completed slot 1/1 ===

DEBUG: Finished processing all slots, 1 successful
DEBUG: About to render 1 lessons
DEBUG: Updating progress tracker for rendering
DEBUG: Progress tracker updated for rendering
DEBUG: Calling _combine_lessons (wrapped in asyncio.to_thread)
DEBUG: _combine_lessons returned: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Daniela_Silva_Lesson_plan_W01_10-20-10-24_20251019_170413.docx
INFO:     127.0.0.1:54914 - "GET /api/progress/cebdce6a-614b-4a8a-b762-a67b778cb7ff/poll HTTP/1.1" 200 OK
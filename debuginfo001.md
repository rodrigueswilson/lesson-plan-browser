INFO:     Will watch for changes in these directories: ['D:\\LP']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [32256] using WatchFiles
INFO:     Started server process [21872]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:51119 - "GET /api/users HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/users/a4e964c6-4090-4c9f-b39c-d47e55bdbe59/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51120 - "GET /api/recent-weeks?user_id=a4e964c6-4090-4c9f-b39c-d47e55bdbe59&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51134 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff HTTP/1.1" 200 OK
INFO:     127.0.0.1:51131 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff/plans?limit=50 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51130 - "GET /api/users/29fa9ed7-3174-4999-86fd-40a542c28cff/slots HTTP/1.1" 200 OK
INFO:     127.0.0.1:51130 - "GET /api/recent-weeks?user_id=29fa9ed7-3174-4999-86fd-40a542c28cff&limit=3 HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "POST /api/process-week HTTP/1.1" 200 OK

============================================================
PROCESS_USER_WEEK STARTED
User: 29fa9ed7-3174-4999-86fd-40a542c28cff
Week: 10-20-10-24
============================================================

DEBUG: About to call db.get_user()
DEBUG: Got user: Daniela Silva
DEBUG: About to call db.get_user_slots()
DEBUG: Got 5 slots
DEBUG: About to start processing 4 slots
DEBUG: Progress tracker updated - starting

DEBUG: === Starting slot 1/4: ELA/SS ===
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
DEBUG: _process_slot - Performance tracking started, op_id: 10e02473-43e0-405f-8dae-9f697586a379
DEBUG: _process_slot - Calling LLM service transform_lesson
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - LLM transform_lesson returned, success: True
DEBUG: _process_slot - Replacing 1 No School days in output
DEBUG: _process_slot completed for slot 1
DEBUG: Appending lesson for slot 1
DEBUG: Lesson appended for slot 1
DEBUG: === Completed slot 1/4 ===

DEBUG: === Starting slot 2/4: Science/Health ===
DEBUG: Updating progress tracker for slot 2
DEBUG: Progress tracker updated for slot 2
DEBUG: About to call _process_slot for slot 2
DEBUG: _process_slot - Resolving primary file for slot 3
DEBUG: _process_slot - Primary file resolved: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Mrs. Grande Science 10_20- 10_24.docx
DEBUG: _process_slot - Creating DOCXParser
DEBUG: _process_slot - DOCXParser created successfully
DEBUG: _process_slot - Extracting images and hyperlinks
DEBUG: _process_slot - Extracted 0 images, 0 hyperlinks
DEBUG: _process_slot - Checking for No School day
DEBUG: _process_slot - Extracting subject content
DEBUG: _process_slot - Content extracted, length: 3472
DEBUG: _process_slot - No School days detected: ['WEDNESDAY']
DEBUG: _process_slot - Starting performance tracking
DEBUG: _process_slot - Performance tracking started, op_id: 33491587-6dd0-4cf2-8287-5cbb370278e0
DEBUG: _process_slot - Calling LLM service transform_lesson
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:51135 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64248 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64248 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - LLM transform_lesson returned, success: True
DEBUG: _process_slot - Replacing 1 No School days in output
DEBUG: _process_slot completed for slot 2
DEBUG: Appending lesson for slot 2
DEBUG: Lesson appended for slot 2
DEBUG: === Completed slot 2/4 ===

DEBUG: === Starting slot 3/4: Science/Health ===
DEBUG: Updating progress tracker for slot 3
DEBUG: Progress tracker updated for slot 3
DEBUG: About to call _process_slot for slot 3
DEBUG: _process_slot - Resolving primary file for slot 4
DEBUG: _process_slot - Primary file resolved: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx
DEBUG: _process_slot - Creating DOCXParser
DEBUG: _process_slot - DOCXParser created successfully
DEBUG: _process_slot - Extracting images and hyperlinks
DEBUG: _process_slot - Extracted 0 images, 16 hyperlinks
DEBUG: _process_slot - Checking for No School day
DEBUG: _process_slot - Extracting subject content
DEBUG: _process_slot - Content extracted, length: 1497
DEBUG: _process_slot - No School days detected: ['WEDNESDAY']
DEBUG: _process_slot - Starting performance tracking
DEBUG: _process_slot - Performance tracking started, op_id: a58c8e27-cb33-4ad7-8648-2318171fa9b8
DEBUG: _process_slot - Calling LLM service transform_lesson
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - LLM transform_lesson returned, success: True
DEBUG: _process_slot - Replacing 1 No School days in output
DEBUG: _process_slot completed for slot 3
DEBUG: Appending lesson for slot 3
DEBUG: Lesson appended for slot 3
DEBUG: === Completed slot 3/4 ===

DEBUG: === Starting slot 4/4: Math ===
DEBUG: Updating progress tracker for slot 4
DEBUG: Progress tracker updated for slot 4
DEBUG: About to call _process_slot for slot 4
DEBUG: _process_slot - Resolving primary file for slot 5
DEBUG: _process_slot - Primary file resolved: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx
DEBUG: _process_slot - Creating DOCXParser
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - DOCXParser created successfully
DEBUG: _process_slot - Extracting images and hyperlinks
DEBUG: _process_slot - Extracted 0 images, 16 hyperlinks
DEBUG: _process_slot - Checking for No School day
DEBUG: _process_slot - Extracting subject content
DEBUG: _process_slot - Content extracted, length: 2084
DEBUG: _process_slot - Starting performance tracking
DEBUG: _process_slot - Performance tracking started, op_id: f9fb9e10-822e-4b92-9258-747e458ac372
DEBUG: _process_slot - Calling LLM service transform_lesson
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _process_slot - LLM transform_lesson returned, success: True
DEBUG: _process_slot completed for slot 4
DEBUG: Appending lesson for slot 4
DEBUG: Lesson appended for slot 4
DEBUG: === Completed slot 4/4 ===

DEBUG: Finished processing all slots, 4 successful
DEBUG: About to render 4 lessons
DEBUG: Updating progress tracker for rendering
DEBUG: Progress tracker updated for rendering
DEBUG: Calling _combine_lessons (wrapped in asyncio.to_thread)
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
DEBUG: _combine_lessons returned: F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Daniela_Silva_Weekly_W43_10-20-10-24_20251019_163729.docx
INFO:     127.0.0.1:64249 - "GET /api/progress/4348f481-4920-4cfe-9ce0-b07139093ff2/poll HTTP/1.1" 200 OK
WARNING:  WatchFiles detected changes in 'check_hyperlinks_now.py'. Reloading...
 INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [21872]
WARNING:  WatchFiles detected changes in 'check_hyperlinks_now.py'. Reloading...
 INFO:     Started server process [20560]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
ERROR:    Traceback (most recent call last):
  File "C:\Users\rodri\AppData\Local\Programs\Python\Python311\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\rodri\AppData\Local\Programs\Python\Python311\Lib\asyncio\base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
asyncio.exceptions.CancelledError

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\LP\.venv\Lib\site-packages\uvicorn\_compat.py", line 23, in asyncio_run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\Users\rodri\AppData\Local\Programs\Python\Python311\Lib\asyncio\runners.py", line 123, in run
    raise KeyboardInterrupt()
KeyboardInterrupt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "D:\LP\.venv\Lib\site-packages\starlette\routing.py", line 701, in lifespan
    await receive()
  File "D:\LP\.venv\Lib\site-packages\uvicorn\lifespan\on.py", line 137, in receive
    return await self.receive_queue.get()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\rodri\AppData\Local\Programs\Python\Python311\Lib\asyncio\queues.py", line 158, in get
    await getter
asyncio.exceptions.CancelledError

INFO:     Started server process [7684]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
WARNING:  WatchFiles detected changes in 'list_daniela_files.py'. Reloading...
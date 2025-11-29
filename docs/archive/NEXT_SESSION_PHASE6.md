# 🚀 Next Session: Phase 6 - FastAPI Backend

**Current Progress:** 75% (6 of 8 phases complete)  
**Next Goal:** Phase 6 - FastAPI Backend  
**Estimated Time:** 4-6 hours

---

## ✅ What's Complete

### Phases 0-5 (All Complete!)
- ✅ **Phase 0:** Observability - Feature flags, telemetry, logging
- ✅ **Phase 1:** JSON Schema - Validation and structure
- ✅ **Phase 2:** Prompt - Dual-mode (JSON + Markdown)
- ✅ **Phase 3:** Templates - Jinja2 rendering system
- ✅ **Phase 4:** Integration - Retry logic, JSON repair, testing
- ✅ **Phase 5:** DOCX Renderer - Convert JSON to formatted DOCX

### Test Status
- **Total Tests:** 25
- **Passing:** 25 (100%)
- **Coverage:** All core functionality

### What Works Right Now
```bash
# Validate JSON
python tools/validate_schema.py tests/fixtures/valid_lesson_minimal.json

# Render to Markdown
python tools/render_lesson_plan.py tests/fixtures/valid_lesson_minimal.json output/test.md

# Render to DOCX
python tools/docx_renderer.py tests/fixtures/valid_lesson_minimal.json output/test.docx

# Run all tests
python tests/test_json_repair.py      # 7/7 passing
python tests/test_pipeline.py         # 3/3 passing
python tests/test_integration.py      # 8/8 passing
python tests/test_docx_renderer.py    # 7/7 passing
```

---

## 🎯 Phase 6 Goals

### FastAPI Backend Implementation

Create a REST API backend that:
1. Accepts lesson plan input (text or JSON)
2. Validates against schema
3. Renders to DOCX format
4. Streams progress via SSE
5. Handles errors gracefully
6. Logs all operations

### Architecture

```
┌─────────────────────────────────────┐
│         Tauri Frontend              │
│      (React + TypeScript)           │
└────────────┬────────────────────────┘
             │ HTTP + SSE
             ↓
┌─────────────────────────────────────┐
│       FastAPI Backend               │
│    (localhost:ephemeral)            │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Endpoints                   │  │
│  │  - POST /api/render          │  │
│  │  - POST /api/validate        │  │
│  │  - GET  /api/health          │  │
│  │  - GET  /api/progress (SSE)  │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Core Pipeline               │  │
│  │  - JSON Schema Validation    │  │ ← Phase 1
│  │  - JSON Repair               │  │ ← Phase 4
│  │  - Retry Logic               │  │ ← Phase 4
│  │  - DOCX Renderer             │  │ ← Phase 5
│  │  - Telemetry                 │  │ ← Phase 0
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## 📋 Phase 6 Implementation Plan

### Task 1: FastAPI Setup (1 hour)

**Create:** `backend/api.py`

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Bilingual Lesson Plan Builder API")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/validate")
async def validate_json(data: dict):
    # Use tools/validate_schema.py
    pass

@app.post("/api/render")
async def render_lesson_plan(data: dict):
    # Use tools/docx_renderer.py
    pass

@app.get("/api/progress")
async def stream_progress():
    # SSE streaming
    pass
```

### Task 2: Request/Response Models (30 min)

**Create:** `backend/models.py`

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class RenderRequest(BaseModel):
    json_data: Dict[str, Any]
    output_filename: Optional[str] = "lesson_plan.docx"

class RenderResponse(BaseModel):
    success: bool
    output_path: Optional[str]
    errors: Optional[list]

class ValidationRequest(BaseModel):
    json_data: Dict[str, Any]

class ValidationResponse(BaseModel):
    valid: bool
    errors: Optional[list]
```

### Task 3: SSE Progress Streaming (1 hour)

**Create:** `backend/progress.py`

```python
import asyncio
from typing import AsyncGenerator

async def stream_progress(task_id: str) -> AsyncGenerator[str, None]:
    """Stream progress updates via SSE."""
    stages = [
        "Validating JSON schema...",
        "Repairing JSON if needed...",
        "Loading template...",
        "Rendering DOCX...",
        "Saving file...",
        "Complete!"
    ]
    
    for stage in stages:
        yield f"data: {stage}\n\n"
        await asyncio.sleep(0.5)
```

### Task 4: Integration with Existing Tools (1 hour)

**Integrate:**
- `tools/validate_schema.py` → `/api/validate`
- `tools/docx_renderer.py` → `/api/render`
- `tools/json_repair.py` → Auto-repair in pipeline
- `backend/telemetry.py` → Log all API calls

### Task 5: Error Handling (30 min)

**Create:** `backend/errors.py`

```python
from fastapi import HTTPException

class ValidationError(HTTPException):
    def __init__(self, errors: list):
        super().__init__(status_code=400, detail={"errors": errors})

class RenderError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=500, detail={"error": message})
```

### Task 6: Testing (1 hour)

**Create:** `tests/test_api.py`

```python
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200

def test_validate_endpoint():
    # Test validation
    pass

def test_render_endpoint():
    # Test rendering
    pass
```

### Task 7: Documentation (30 min)

**Create:** `PHASE6_IMPLEMENTATION.md`

---

## 🔧 Technical Requirements

### Dependencies

Add to `requirements_phase6.txt`:
```
# Previous phases
jsonschema>=4.17.0
jinja2>=3.1.2
pydantic>=2.0.0
pydantic-settings>=2.0.0
structlog>=23.1.0
python-dotenv>=1.0.0
python-docx>=0.8.11

# Phase 6 additions
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sse-starlette>=1.6.5
python-multipart>=0.0.6
```

### Configuration

Update `backend/config.py`:
```python
class APIConfig(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 0  # Ephemeral port
    log_level: str = "info"
    cors_origins: list = ["tauri://localhost"]
```

---

## 🧪 Testing Strategy

### Unit Tests
- Test each endpoint independently
- Mock external dependencies
- Verify error handling

### Integration Tests
- Test full pipeline (validate → render)
- Test SSE streaming
- Test error scenarios

### Performance Tests
- Measure API response times
- Test concurrent requests
- Verify p95 < 3s target

---

## 📊 Success Criteria

Phase 6 complete when:
- ✅ All API endpoints implemented
- ✅ SSE progress streaming working
- ✅ Integration with Phases 0-5 complete
- ✅ Error handling comprehensive
- ✅ Tests passing (target: 10+ tests)
- ✅ Documentation complete
- ✅ Performance targets met

---

## 🚀 Quick Start Commands

### Install Dependencies
```bash
pip install -r requirements_phase6.txt
```

### Run API Server
```bash
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

### Test API
```bash
# Health check
curl http://localhost:8000/api/health

# Validate JSON
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/valid_lesson_minimal.json

# Render DOCX
curl -X POST http://localhost:8000/api/render \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/valid_lesson_minimal.json \
  --output lesson_plan.docx
```

### Run Tests
```bash
pytest tests/test_api.py -v
```

---

## 💡 Key Considerations

### 1. Ephemeral Port Binding
- Use port 0 to get random available port
- Return actual port to frontend
- Avoid port conflicts

### 2. SSE Backpressure
- Implement proper SSE streaming
- Handle client disconnects
- Buffer management

### 3. File Management
- Temporary file handling
- Cleanup after rendering
- Secure file paths

### 4. Error Handling
- Validation errors (400)
- Rendering errors (500)
- Detailed error messages
- Telemetry logging

### 5. Performance
- Async/await for I/O
- Background tasks for rendering
- Response streaming
- Target: p95 < 3s

---

## 📁 Files to Create

### Core Implementation
1. `backend/api.py` - Main FastAPI app
2. `backend/models.py` - Request/response models
3. `backend/progress.py` - SSE streaming
4. `backend/errors.py` - Error handling

### Testing
5. `tests/test_api.py` - API endpoint tests

### Documentation
6. `PHASE6_IMPLEMENTATION.md` - Implementation guide
7. `requirements_phase6.txt` - Dependencies

---

## 🎯 After Phase 6

### Phase 7: End-to-End Testing
- Integration tests across all components
- Performance benchmarking
- User acceptance testing
- Bug fixes and refinements

### Phase 8: Migration & Deployment
- Migrate from markdown to JSON pipeline
- Production deployment
- User training
- Documentation finalization

---

## 📈 Progress Tracking

```
Current:  ███████████████░░░░░ 75%
After P6: ██████████████████░░ 87.5%
After P7: ████████████████████ 100%
```

---

## 🎉 Ready to Start Phase 6!

All prerequisites are in place:
- ✅ JSON validation (Phase 1)
- ✅ DOCX rendering (Phase 5)
- ✅ Error handling (Phase 4)
- ✅ Telemetry (Phase 0)
- ✅ Test infrastructure (Phase 4)

**Let's build the FastAPI backend!** 🚀

---

*Created: 2025-10-04 22:14 PM*  
*For: Next session (Phase 6)*  
*Current Progress: 75%*

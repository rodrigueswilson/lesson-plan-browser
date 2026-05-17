# Feature Enhancement Plan - Bilingual Weekly Plan Builder

**Created**: 2025-10-18  
**Status**: PARTIAL – many features implemented; remainder planned (see Status section below).  
**Priority**: HIGH - User Experience & Research Capabilities

---

## Status (implemented vs remaining)

**Implemented** (see [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)): 1 (table widths), 3 (No School), 5 (timestamped filenames), 6 (performance tracking), 7 (slot checkboxes), 9 (button state), 10 (progress bar), 12 (file open / show in folder), 13 (analytics dashboard).

**Remaining (planned):** 2 (image preservation), 4 (hyperlink preservation), 8 (source folder path confirmation), 11 (session-based history view). For roadmap index see [../roadmap/README.md](../roadmap/README.md).

---

## 📋 Overview

This document outlines the implementation plan for 13 feature enhancements across document processing, GUI/frontend, and analytics/research capabilities.

---

## 🎯 Feature Categories

### Category A: Document Processing (6 features)
1. Equal table width enforcement
2. Image preservation from input to output
3. "No School" day handling
4. Hyperlink preservation
5. Timestamped output filenames
6. Performance measurement tool

### Category B: GUI/Frontend (7 features)
7. Slot-level reprocessing checkboxes
8. Source folder path confirmation
9. Processing button state improvements
10. Progress bar real-time updates
11. Session-based history view
12. File location & direct open actions
13. Integrated analytics dashboard

---

## 🔍 Pre-Implementation Assessment

### Existing Code Analysis

**Files Requiring Updates:**

| Feature | Affected Files | Complexity | Dependencies |
|---------|---------------|------------|--------------|
| 1. Table widths | `tools/docx_renderer.py` | Low | python-docx |
| 2. Images | `tools/docx_parser.py`, `tools/docx_renderer.py` | Medium | python-docx |
| 3. No School | `tools/batch_processor.py`, `backend/api.py` | Low | None |
| 4. Hyperlinks | `tools/docx_parser.py`, `tools/docx_renderer.py` | Medium | python-docx |
| 5. Timestamps | `backend/file_manager.py`, `tools/docx_renderer.py` | Low | datetime |
| 6. Performance | NEW: `backend/performance_tracker.py` | High | SQLite |
| 7. Checkboxes | `frontend/src/components/SlotConfigurator.tsx` | Low | React state |
| 8. Path confirm | `frontend/src/components/BatchProcessor.tsx` | Low | Tauri API |
| 9. Button state | `frontend/src/components/BatchProcessor.tsx` | Low | React state |
| 10. Progress | `frontend/src/components/BatchProcessor.tsx` | Medium | SSE |
| 11. History | `frontend/src/components/PlanHistory.tsx` | Medium | SQLite |
| 12. File actions | `frontend/src/components/PlanHistory.tsx` | Medium | Tauri API |
| 13. Analytics | NEW: `frontend/src/components/Analytics.tsx` | High | Performance DB |

### Coding Principles Compliance

**DRY**: Extract common DOCX operations into utility module  
**SSOT**: Centralize filename generation logic  
**KISS**: Implement simple solutions first, avoid over-engineering  
**SOLID**: Separate concerns (parsing, rendering, tracking)  
**YAGNI**: Only implement requested features, no speculation

---

## 📅 Implementation Sessions

### Session 1: Document Processing Foundation (3-4 hours)
**Features**: 1, 2, 4, 5  
**Focus**: DOCX parsing and rendering enhancements

### Session 2: Workflow Intelligence (2-3 hours)
**Features**: 3, 6  
**Focus**: Special case handling and performance tracking

### Session 3: Frontend UX Improvements (3-4 hours)
**Features**: 7, 8, 9, 10  
**Focus**: User interface enhancements

### Session 4: History & Analytics (3-4 hours)
**Features**: 11, 12, 13  
**Focus**: Data management and research capabilities

### Session 5: Integration & Testing (2-3 hours)
**Focus**: End-to-end testing, documentation, deployment

---

## 🎯 Session 1: Document Processing Foundation

### Objectives
- Ensure consistent table formatting
- Preserve images from input
- Preserve hyperlinks
- Add timestamps to filenames

### Implementation Plan

#### Feature 1: Equal Table Widths
**File**: `tools/docx_renderer.py`

**Current Issue**: Tables may have inconsistent widths  
**Solution**: Set explicit column widths based on template

**Implementation**:
```python
# New method in DOCXRenderer class
def _normalize_table_widths(self, table: Table) -> None:
    """Ensure all columns have equal width."""
    total_width = table.width
    num_cols = len(table.columns)
    col_width = total_width // num_cols
    
    for column in table.columns:
        column.width = col_width
```

**Testing**: Verify all output tables have equal column widths

---

#### Feature 2: Image Preservation
**Files**: `tools/docx_parser.py`, `tools/docx_renderer.py`

**Current Issue**: Images in input are not extracted or preserved  
**Solution**: Extract images during parsing, embed in output

**Implementation**:

1. **Parser Enhancement** (`docx_parser.py`):
```python
def extract_images(self) -> List[Dict[str, Any]]:
    """Extract all images from document with metadata."""
    images = []
    for rel in self.doc.part.rels.values():
        if "image" in rel.target_ref:
            images.append({
                'data': rel.target_part.blob,
                'content_type': rel.target_part.content_type,
                'filename': rel.target_ref.split('/')[-1]
            })
    return images
```

2. **Renderer Enhancement** (`docx_renderer.py`):
```python
def _insert_image(self, paragraph, image_data: bytes, width_inches: float = 3.0):
    """Insert image into paragraph."""
    from io import BytesIO
    run = paragraph.add_run()
    run.add_picture(BytesIO(image_data), width=Inches(width_inches))
```

**Testing**: Input with images produces output with same images

---

#### Feature 4: Hyperlink Preservation
**Files**: `tools/docx_parser.py`, `tools/docx_renderer.py`

**Current Issue**: Hyperlinks are converted to plain text  
**Solution**: Extract and preserve hyperlink relationships

**Implementation**:

1. **Parser Enhancement**:
```python
def extract_hyperlinks(self) -> List[Dict[str, str]]:
    """Extract all hyperlinks with text and URL."""
    hyperlinks = []
    for paragraph in self.doc.paragraphs:
        for hyperlink in paragraph.hyperlinks:
            hyperlinks.append({
                'text': hyperlink.text,
                'url': hyperlink.address,
                'context': paragraph.text
            })
    return hyperlinks
```

2. **Renderer Enhancement**:
```python
def _add_hyperlink(self, paragraph, text: str, url: str):
    """Add hyperlink to paragraph."""
    # Implementation using python-docx hyperlink support
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = docx.oxml.shared.OxmlElement('w:hyperlink')
    hyperlink.set(docx.oxml.shared.qn('r:id'), r_id)
    # Add run with text
```

**Testing**: Hyperlinks remain clickable in output

---

#### Feature 5: Timestamped Filenames
**Files**: `backend/file_manager.py`, `tools/docx_renderer.py`

**Current Issue**: Filenames may overwrite previous versions  
**Solution**: Append timestamp to filename

**Implementation**:

1. **Create Utility Function** (`backend/file_manager.py`):
```python
def generate_timestamped_filename(base_name: str, extension: str = ".docx") -> str:
    """Generate filename with timestamp.
    
    Args:
        base_name: Base filename without extension
        extension: File extension (default: .docx)
    
    Returns:
        Filename with timestamp: {base_name}_YYYYMMDD_HHMMSS{extension}
    """
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}{extension}"
```

2. **Update Renderer** (`tools/docx_renderer.py`):
```python
# In render() method
from backend.file_manager import generate_timestamped_filename

output_filename = generate_timestamped_filename(
    f"{user_name}_Weekly_W{week_num}_{week_of}"
)
```

**Testing**: Multiple runs create unique filenames

---

### Deliverables
- [ ] Updated `tools/docx_renderer.py` with table width normalization
- [ ] Updated `tools/docx_parser.py` with image extraction
- [ ] Updated `tools/docx_renderer.py` with image insertion
- [ ] Updated `tools/docx_parser.py` with hyperlink extraction
- [ ] Updated `tools/docx_renderer.py` with hyperlink insertion
- [ ] New utility function for timestamped filenames
- [ ] Unit tests for all new functions
- [ ] Integration test with real DOCX files

---

## 🎯 Session 2: Workflow Intelligence

### Objectives
- Handle "No School" days gracefully
- Implement comprehensive performance tracking

### Implementation Plan

#### Feature 3: "No School" Day Handling
**Files**: `tools/batch_processor.py`, `backend/api.py`

**Current Issue**: System processes "No School" days unnecessarily  
**Solution**: Detect "No School" and copy input to output

**Implementation**:

1. **Detection Logic** (`tools/docx_parser.py`):
```python
def is_no_school_day(self) -> bool:
    """Check if document indicates 'No School' day."""
    no_school_patterns = [
        r'no\s+school',
        r'school\s+closed',
        r'holiday',
        r'professional\s+development',
        r'teacher\s+workday'
    ]
    
    full_text = self.get_full_text().lower()
    return any(re.search(pattern, full_text) for pattern in no_school_patterns)
```

2. **Batch Processor Update** (`tools/batch_processor.py`):
```python
def process_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process single slot, handling No School days."""
    parser = DOCXParser(slot_data['input_file'])
    
    if parser.is_no_school_day():
        # Copy input to output without processing
        import shutil
        output_path = self._generate_output_path(slot_data)
        shutil.copy2(slot_data['input_file'], output_path)
        
        return {
            'status': 'skipped',
            'reason': 'no_school_day',
            'output_file': output_path
        }
    
    # Normal processing...
```

**Testing**: "No School" input produces unmodified copy

---

#### Feature 6: Performance Measurement Tool
**Files**: NEW `backend/performance_tracker.py`, `backend/database.py`

**Current Issue**: No systematic performance tracking  
**Solution**: Comprehensive timing and metrics database

**Implementation**:

1. **Database Schema** (`backend/database.py`):
```sql
CREATE TABLE performance_metrics (
    id TEXT PRIMARY KEY,
    plan_id TEXT,
    operation_type TEXT,  -- 'parse', 'llm_call', 'render', 'total'
    start_time REAL,
    end_time REAL,
    duration_ms REAL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    llm_model TEXT,
    cost_usd REAL,
    metadata TEXT,  -- JSON for additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id)
);

CREATE INDEX idx_perf_plan ON performance_metrics(plan_id);
CREATE INDEX idx_perf_operation ON performance_metrics(operation_type);
```

2. **Performance Tracker** (`backend/performance_tracker.py`):
```python
from contextlib import contextmanager
from time import time
from typing import Optional, Dict, Any
import json

class PerformanceTracker:
    """Track performance metrics for research and optimization."""
    
    def __init__(self, db: Database):
        self.db = db
    
    @contextmanager
    def track_operation(
        self,
        operation_type: str,
        plan_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Context manager to track operation timing."""
        start_time = time()
        metric_id = str(uuid.uuid4())
        
        try:
            yield metric_id
        finally:
            end_time = time()
            duration_ms = (end_time - start_time) * 1000
            
            self.db.record_performance_metric(
                metric_id=metric_id,
                plan_id=plan_id,
                operation_type=operation_type,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                metadata=json.dumps(metadata) if metadata else None
            )
    
    def record_llm_call(
        self,
        plan_id: str,
        model: str,
        tokens_input: int,
        tokens_output: int,
        duration_ms: float,
        cost_usd: float
    ):
        """Record LLM API call metrics."""
        # Implementation...
    
    def get_plan_metrics(self, plan_id: str) -> Dict[str, Any]:
        """Get all metrics for a plan."""
        # Implementation...
    
    def get_aggregate_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregate statistics for research."""
        # Implementation...
```

3. **Integration** (`tools/batch_processor.py`, `backend/llm_service.py`):
```python
# In batch_processor.py
with tracker.track_operation('parse', plan_id, {'slot': slot_num}):
    lesson_data = parser.parse()

with tracker.track_operation('llm_call', plan_id):
    result = llm_service.transform(lesson_data)

with tracker.track_operation('render', plan_id):
    renderer.render(result, output_path)
```

**Testing**: All operations recorded with accurate timing

---

### Deliverables
- [ ] "No School" detection in parser
- [ ] Batch processor handles "No School" days
- [ ] Performance tracker module
- [ ] Database schema for metrics
- [ ] Integration with all major operations
- [ ] API endpoints for metrics retrieval
- [ ] Unit tests for performance tracking

---

## 🎯 Session 3: Frontend UX Improvements

### Objectives
- Add slot-level reprocessing controls
- Improve path confirmation
- Fix processing button states
- Fix progress bar updates

### Implementation Plan

#### Feature 7: Slot Reprocessing Checkboxes
**File**: `frontend/src/components/SlotConfigurator.tsx`

**Current Issue**: Cannot selectively reprocess slots  
**Solution**: Add checkbox to each slot

**Implementation**:
```typescript
// Add to slot state
interface ClassSlot {
  // ... existing fields
  selected: boolean;  // NEW
}

// In SlotConfigurator component
<div className="flex items-center gap-2">
  <input
    type="checkbox"
    checked={slot.selected}
    onChange={(e) => updateSlot(slot.id, { selected: e.target.checked })}
    className="w-4 h-4"
  />
  <Label>Slot {slot.slot_number}: {slot.subject}</Label>
</div>

// Update batch processor to only process selected slots
const selectedSlots = slots.filter(s => s.selected);
```

**Testing**: Only selected slots are processed

---

#### Feature 8: Source Folder Path Confirmation
**File**: `frontend/src/components/BatchProcessor.tsx`

**Current Issue**: User cannot verify source folder  
**Solution**: Replace week input with folder path confirmation

**Implementation**:
```typescript
import { open } from '@tauri-apps/api/dialog';
import { invoke } from '@tauri-apps/api/tauri';

const [sourcePath, setSourcePath] = useState('');
const [weekOf, setWeekOf] = useState('');

const selectSourceFolder = async () => {
  const selected = await open({
    directory: true,
    multiple: false,
    title: 'Select Week Folder with Input Lesson Plans'
  });
  
  if (selected && typeof selected === 'string') {
    setSourcePath(selected);
    // Auto-detect week_of from folder name or files
    const detectedWeek = await invoke('detect_week_from_folder', { path: selected });
    setWeekOf(detectedWeek);
  }
};

// UI
<div className="space-y-2">
  <Label>Source Folder</Label>
  <div className="flex gap-2">
    <Input value={sourcePath} readOnly placeholder="No folder selected" />
    <Button onClick={selectSourceFolder}>Browse...</Button>
  </div>
  {weekOf && <p className="text-sm text-muted-foreground">Detected: Week of {weekOf}</p>}
</div>
```

**Testing**: Folder selection works, week detection accurate

---

#### Feature 9: Processing Button State
**File**: `frontend/src/components/BatchProcessor.tsx`

**Current Issue**: Button spinner doesn't stop properly  
**Solution**: Clear state management with completion indicator

**Implementation**:
```typescript
const [processingState, setProcessingState] = useState<'idle' | 'processing' | 'done' | 'error'>('idle');

// In handleProcess
setProcessingState('processing');

// When complete
if (data.status === 'completed') {
  setProcessingState('done');
  setTimeout(() => setProcessingState('idle'), 3000); // Reset after 3s
} else {
  setProcessingState('error');
}

// Button rendering
<Button onClick={handleProcess} disabled={processingState !== 'idle'}>
  {processingState === 'idle' && <Play className="w-4 h-4 mr-2" />}
  {processingState === 'processing' && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
  {processingState === 'done' && <CheckCircle2 className="w-4 h-4 mr-2" />}
  {processingState === 'error' && <XCircle className="w-4 h-4 mr-2" />}
  
  {processingState === 'idle' && 'Process'}
  {processingState === 'processing' && 'Processing...'}
  {processingState === 'done' && 'Done!'}
  {processingState === 'error' && 'Failed'}
</Button>
```

**Testing**: Button shows correct state at each stage

---

#### Feature 10: Progress Bar Real-Time Updates
**File**: `frontend/src/components/BatchProcessor.tsx`

**Current Issue**: Progress bar stuck on "Starting..."  
**Solution**: Properly handle SSE progress events

**Implementation**:
```typescript
// Fix SSE event handling
const eventSource = createProgressStream(response.data.plan_id, (data) => {
  console.log('Progress update:', data); // Debug
  
  setProgress({
    current: data.current || 0,
    total: data.total || slots.length,
    message: data.message || 'Processing...',
    percentage: data.percentage || 0  // NEW
  });
  
  // Update processing state
  if (data.status === 'completed') {
    eventSource.close();
    setProcessingState('done');
    setResult(data);
  } else if (data.status === 'failed') {
    eventSource.close();
    setProcessingState('error');
    setError(data.error);
  }
});

// Progress display
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span>{progress.message}</span>
    <span>{progress.current}/{progress.total}</span>
  </div>
  <Progress value={progress.percentage} />
</div>
```

**Testing**: Progress updates in real-time during processing

---

### Deliverables
- [ ] Slot checkboxes in configurator
- [ ] Folder selection dialog
- [ ] Week detection from folder
- [ ] Button state machine
- [ ] Fixed SSE progress handling
- [ ] Visual feedback for all states
- [ ] Unit tests for components

---

## 🎯 Session 4: History & Analytics

### Objectives
- Implement session-based history
- Add file location and open actions
- Create analytics dashboard

### Implementation Plan

#### Feature 11: Session-Based History View
**File**: `frontend/src/components/PlanHistory.tsx`

**Current Issue**: History shows all plans, too long  
**Solution**: Show current session, with option to view all

**Implementation**:
```typescript
const [viewMode, setViewMode] = useState<'session' | 'all'>('session');
const [sessionStart] = useState(new Date());

const filteredPlans = viewMode === 'session'
  ? plans.filter(p => new Date(p.generated_at) >= sessionStart)
  : plans;

// UI
<div className="flex justify-between items-center mb-4">
  <CardTitle>Plan History</CardTitle>
  <div className="flex gap-2">
    <Button
      variant={viewMode === 'session' ? 'default' : 'outline'}
      size="sm"
      onClick={() => setViewMode('session')}
    >
      This Session ({sessionPlans.length})
    </Button>
    <Button
      variant={viewMode === 'all' ? 'default' : 'outline'}
      size="sm"
      onClick={() => setViewMode('all')}
    >
      All History ({plans.length})
    </Button>
  </div>
</div>
```

**Testing**: Session filter works correctly

---

#### Feature 12: File Location & Open Actions
**File**: `frontend/src/components/PlanHistory.tsx`

**Current Issue**: Download button doesn't work  
**Solution**: Add "Open Location" and "Open File" buttons

**Implementation**:
```typescript
import { invoke } from '@tauri-apps/api/tauri';

const openFileLocation = async (filePath: string) => {
  try {
    await invoke('show_in_folder', { path: filePath });
  } catch (err) {
    console.error('Failed to open location:', err);
  }
};

const openFile = async (filePath: string) => {
  try {
    await invoke('open_file', { path: filePath });
  } catch (err) {
    console.error('Failed to open file:', err);
  }
};

// UI - replace download button
{plan.status === 'completed' && plan.output_file && (
  <div className="flex gap-2">
    <Button
      variant="outline"
      size="sm"
      onClick={() => openFileLocation(plan.output_file!)}
      title="Show in folder"
    >
      <FolderOpen className="w-4 h-4" />
    </Button>
    <Button
      variant="outline"
      size="sm"
      onClick={() => openFile(plan.output_file!)}
      title="Open document"
    >
      <FileText className="w-4 h-4" />
    </Button>
  </div>
)}
```

**Rust Backend** (`src-tauri/src/main.rs`):
```rust
#[tauri::command]
fn show_in_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    // macOS and Linux implementations...
    Ok(())
}

#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    opener::open(path).map_err(|e| e.to_string())
}
```

**Testing**: Both actions work on all platforms

---

#### Feature 13: Integrated Analytics Dashboard
**Files**: NEW `frontend/src/components/Analytics.tsx`, `backend/api.py`

**Current Issue**: No visibility into performance metrics  
**Solution**: Comprehensive analytics dashboard

**Implementation**:

1. **Backend API** (`backend/api.py`):
```python
@app.get("/api/analytics/summary")
async def get_analytics_summary(
    days: int = 30,
    user_id: Optional[str] = None
):
    """Get analytics summary for research."""
    tracker = PerformanceTracker(db)
    return tracker.get_aggregate_stats(days, user_id)

@app.get("/api/analytics/plan/{plan_id}")
async def get_plan_analytics(plan_id: str):
    """Get detailed metrics for specific plan."""
    tracker = PerformanceTracker(db)
    return tracker.get_plan_metrics(plan_id)
```

2. **Frontend Component** (`Analytics.tsx`):
```typescript
interface AnalyticsData {
  totalPlans: number;
  avgProcessingTime: number;
  totalTokensUsed: number;
  totalCost: number;
  avgCostPerPlan: number;
  modelDistribution: Record<string, number>;
  operationBreakdown: {
    parse: number;
    llm: number;
    render: number;
  };
}

export const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState(30);
  
  // Fetch and display analytics
  // Charts using recharts or similar library
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Analytics</CardTitle>
        <CardDescription>
          Research data for the last {timeRange} days
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            title="Total Plans"
            value={data?.totalPlans}
            icon={<FileText />}
          />
          <MetricCard
            title="Avg Processing Time"
            value={`${data?.avgProcessingTime.toFixed(1)}s`}
            icon={<Clock />}
          />
          <MetricCard
            title="Total Tokens"
            value={data?.totalTokensUsed.toLocaleString()}
            icon={<Zap />}
          />
          <MetricCard
            title="Total Cost"
            value={`$${data?.totalCost.toFixed(2)}`}
            icon={<DollarSign />}
          />
        </div>
        
        {/* Charts for operation breakdown, model distribution, etc. */}
      </CardContent>
    </Card>
  );
};
```

**Testing**: Dashboard displays accurate metrics

---

### Deliverables
- [ ] Session-based history filtering
- [ ] File location and open actions
- [ ] Tauri commands for file operations
- [ ] Analytics backend API
- [ ] Analytics frontend component
- [ ] Charts and visualizations
- [ ] Export functionality for research data
- [ ] Unit and integration tests

---

## 🎯 Session 5: Integration & Testing

### Objectives
- End-to-end testing of all features
- Documentation updates
- Deployment preparation

### Tasks
1. Integration testing with real data
2. Performance benchmarking
3. Update user documentation
4. Update API documentation
5. Create migration guide
6. Update deployment checklist
7. Create feature demo video
8. Prepare release notes

---

## 📊 Success Criteria

### Functional Requirements
- [ ] All table widths equal in output
- [ ] Images preserved from input to output
- [ ] "No School" days handled correctly
- [ ] Hyperlinks remain clickable
- [ ] Filenames include timestamps
- [ ] Performance metrics recorded
- [ ] Slot checkboxes functional
- [ ] Folder selection works
- [ ] Button states correct
- [ ] Progress bar updates in real-time
- [ ] Session history filters work
- [ ] File actions work on all platforms
- [ ] Analytics dashboard displays data

### Non-Functional Requirements
- [ ] All code follows DRY, SSOT, KISS, SOLID, YAGNI
- [ ] No duplicate code
- [ ] All functions have single responsibility
- [ ] Configuration centralized
- [ ] All tests passing
- [ ] Performance within targets
- [ ] Documentation complete

---

## 🔧 Technical Considerations

### Database Schema Changes
```sql
-- Add to weekly_plans table
ALTER TABLE weekly_plans ADD COLUMN processing_time_ms REAL;
ALTER TABLE weekly_plans ADD COLUMN tokens_used INTEGER;
ALTER TABLE weekly_plans ADD COLUMN cost_usd REAL;
ALTER TABLE weekly_plans ADD COLUMN llm_model TEXT;

-- New performance_metrics table (see Session 2)
```

### Configuration Updates
```python
# backend/config.py
class Settings(BaseSettings):
    # ... existing settings
    
    # Performance tracking
    ENABLE_PERFORMANCE_TRACKING: bool = True
    PERFORMANCE_DB_PATH: str = "data/performance.db"
    
    # File naming
    FILENAME_TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"
    
    # No School detection
    NO_SCHOOL_PATTERNS: List[str] = [
        "no school", "school closed", "holiday",
        "professional development", "teacher workday"
    ]
```

### API Changes
```python
# New endpoints
POST /api/plans/process-selected  # Process only selected slots
GET /api/analytics/summary
GET /api/analytics/plan/{plan_id}
GET /api/analytics/export  # Export for research
```

---

## 📝 Documentation Updates Required

1. **README.md** - Add new features section
2. **QUICK_START_GUIDE.md** - Update with new UI elements
3. **USER_TRAINING_GUIDE.md** - Add analytics section
4. **API_REFERENCE.md** - Document new endpoints
5. **ARCHITECTURE.md** - Add performance tracking module
6. **DEPLOYMENT_CHECKLIST.md** - Add database migration steps

---

## 🚀 Deployment Strategy

### Phase 1: Backend Features (Sessions 1-2)
- Deploy document processing enhancements
- Deploy performance tracking
- Minimal frontend changes

### Phase 2: Frontend Features (Session 3)
- Deploy UI improvements
- Requires frontend rebuild

### Phase 3: Analytics (Session 4)
- Deploy analytics dashboard
- Requires both backend and frontend

### Phase 4: Final Integration (Session 5)
- Full system deployment
- User training
- Documentation release

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Image extraction complexity | Medium | Use python-docx built-in methods |
| Hyperlink preservation | Medium | Test with multiple DOCX formats |
| Performance overhead | Low | Make tracking optional via config |
| Frontend-backend sync | Medium | Version API endpoints |
| Cross-platform file ops | High | Test on Windows, macOS, Linux |

---

## 📚 References

- python-docx documentation: https://python-docx.readthedocs.io/
- Tauri API: https://tauri.app/v1/api/js/
- React best practices: https://react.dev/
- SQLite performance: https://www.sqlite.org/optoverview.html

---

**Status**: Ready for Review  
**Next Step**: Review plan with team, then proceed to Session 1  
**Estimated Total Time**: 13-18 hours across 5 sessions

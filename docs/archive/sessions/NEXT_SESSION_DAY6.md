# Next Session - Day 6: Analytics Dashboard

**Status**: READY TO START  
**Estimated Time**: 2-3 hours  
**Prerequisites**: Session 5 complete (Images + Hyperlinks ✅)

---

## 🎯 Session Goal

Implement the final feature: **Analytics Dashboard** for visualizing performance metrics.

---

## 📋 What You Need to Know

### Current Status
- ✅ 12/13 features complete (92%)
- ✅ Performance tracking already collecting data (Session 2)
- ✅ Database has `performance_metrics` table with rich data
- ✅ Backend has `PerformanceTracker` with query methods
- ❌ No visual dashboard yet (data exists but not visualized)

### What's Missing
- Backend API endpoints for analytics data
- Frontend Analytics component with charts
- CSV export functionality

---

## 🚀 Implementation Plan

### Part 1: Backend API (30 minutes)

**File**: `backend/api.py`

Add these endpoints:

```python
@app.get("/api/analytics/summary")
async def get_analytics_summary(
    user_id: Optional[str] = None,
    days: int = 30
):
    """Get aggregate analytics summary."""
    tracker = get_tracker()
    return tracker.get_aggregate_stats(days, user_id)

@app.get("/api/analytics/daily")
async def get_daily_analytics(
    user_id: Optional[str] = None,
    days: int = 30
):
    """Get daily breakdown of activity."""
    tracker = get_tracker()
    return tracker.get_daily_breakdown(days, user_id)

@app.get("/api/analytics/export")
async def export_analytics(
    user_id: Optional[str] = None,
    days: int = 30
):
    """Export analytics to CSV."""
    tracker = get_tracker()
    csv_data = tracker.export_to_csv(days, user_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=analytics.csv"
        }
    )
```

**Note**: `PerformanceTracker` methods already exist from Session 2!

### Part 2: Frontend Setup (10 minutes)

**Install recharts**:
```bash
cd frontend
npm install recharts
```

### Part 3: Analytics Component (90 minutes)

**File**: `frontend/src/components/Analytics.tsx` (NEW)

**Structure**:
1. Summary Cards (4 cards)
   - Total Plans
   - Average Time
   - Total Tokens
   - Total Cost

2. Charts (3 charts)
   - Pie Chart: Model distribution
   - Bar Chart: Operation breakdown (parse/llm/render)
   - Line Chart: Daily activity

3. Controls
   - Time range selector (7/30/90 days)
   - User filter (optional)
   - Export CSV button

**Sample Code**:
```tsx
import { PieChart, Pie, BarChart, Bar, LineChart, Line } from 'recharts';

export function Analytics() {
  const [timeRange, setTimeRange] = useState(30);
  const [summary, setSummary] = useState(null);
  
  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);
  
  const fetchAnalytics = async () => {
    const data = await api.getAnalyticsSummary(timeRange);
    setSummary(data);
  };
  
  const exportCSV = async () => {
    const blob = await api.exportAnalytics(timeRange);
    // Download logic
  };
  
  return (
    <div className="analytics-dashboard">
      {/* Summary cards */}
      {/* Charts */}
      {/* Export button */}
    </div>
  );
}
```

### Part 4: Integration (30 minutes)

**File**: `frontend/src/App.tsx`

Add Analytics tab/section:
```tsx
<Tab value="analytics">
  <Analytics />
</Tab>
```

**File**: `frontend/src/lib/api.ts`

Add API methods:
```typescript
export const api = {
  // ... existing methods
  
  getAnalyticsSummary: async (days: number) => {
    return invoke('http_request', {
      method: 'GET',
      url: `${API_BASE}/analytics/summary?days=${days}`
    });
  },
  
  exportAnalytics: async (days: number) => {
    return invoke('http_request', {
      method: 'GET',
      url: `${API_BASE}/analytics/export?days=${days}`
    });
  }
};
```

---

## 📊 Data Available

The `performance_metrics` table already has:
- `plan_id`: Link to weekly plan
- `operation_type`: parse_slot, process_slot, render_document
- `duration_ms`: Time taken
- `tokens_input`, `tokens_output`: Token usage
- `llm_model`, `llm_provider`: Model info
- `metadata`: JSON with additional context
- `created_at`: Timestamp

The `weekly_plans` table has:
- `total_time_ms`: Total processing time
- `total_tokens_input`, `total_tokens_output`: Aggregate tokens
- `total_cost_usd`: Total cost

---

## ✅ Success Criteria

When done, you'll have:
- [ ] Backend API endpoints working
- [ ] Analytics component rendering
- [ ] Summary cards showing correct data
- [ ] 3 charts displaying metrics
- [ ] CSV export downloading
- [ ] Time range selector working
- [ ] All 13 features complete (100%)

---

## 🎉 After This Session

The app will be **100% feature-complete** with all 13 planned enhancements:

### Document Processing (4/4) ✅
1. Equal table widths
2. Image preservation
3. Hyperlink preservation
4. Timestamped filenames

### Workflow Intelligence (2/2) ✅
5. "No School" day handling
6. Performance tracking

### Frontend UX (4/4) ✅
7. Slot-level reprocessing
8. Folder path confirmation
9. Button state improvements
10. Progress updates

### Analytics & History (3/3) ✅
11. History view
12. File operations
13. Analytics dashboard

---

## 💡 Tips

1. **Use Existing Methods**: `PerformanceTracker` already has all query methods
2. **Recharts Docs**: https://recharts.org/en-US/examples
3. **CSV Download**: Use `URL.createObjectURL()` for blob download
4. **Responsive Design**: Make charts responsive with `ResponsiveContainer`
5. **Loading States**: Show loading spinner while fetching data

---

## 📝 Quick Start Commands

```bash
# Install dependencies
cd frontend
npm install recharts

# Start backend (if not running)
cd ..
python -m backend.api

# Start frontend (if not running)
cd frontend
npm run tauri dev
```

---

**Ready to complete the final feature? Let's build the Analytics Dashboard!**

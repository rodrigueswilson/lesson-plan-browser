# Tablet Tab - Quick Summary

## Goal
Add a "Tablet" tab to the PC app that allows each user to update **only their own** database for tablet deployment.

## Terminology

- “Current user” here means the **selected user** in `UserSelector` (`useStore().currentUser`). There is no real authentication yet.

## Key Difference from Current Scripts

### Current Behavior
- `sync-database-to-tablet.ps1` → Updates **all users** in the database
- Script can filter with `--user` parameter, but requires manual specification

### New Behavior
- "Tablet" tab → Updates **only the current logged-in user**
- User ID is automatically determined from the app's current user selection
- No need to manually specify user ID
 - **Exports a user-only tablet DB file** (one SQLite file per user) for privacy and smaller APK bundling

## Implementation Overview

### 1. Navigation
- Add "Tablet" to navigation menu (with Tablet icon from lucide-react)
- Add route handler in App.tsx

### 2. TabletSync Component
- Shows current user info
- "Sync My Database" button (only enabled when user is selected)
- Sync options (include-existing, plan-limit, timeout)
- Real-time progress display
- Results summary
 - **Export button**: produce `data/tablet_db_exports/<user_id>/lesson_planner.db`

### 3. Tauri Command
**Recommended**: implement this as a **backend API endpoint** (Python FastAPI), since the backend is already running and already owns Python dependencies.

- `POST /api/tablet/sync` with `user_id`, `include_existing`, `plan_limit`, `timeout`
- Backend runs the sync for exactly one user (equivalent to `--user <current_user_id>`)
 - `POST /api/tablet/export-db` with `user_id`
   - Backend clones schema for tablet tables and copies only this user’s rows into a new SQLite file

Alternative: reuse the existing Rust↔Python **sidecar IPC** pattern (like `trigger_sync`) and add a `"tablet_db_sync"` command.

### 4. No Python Script Changes Needed
- Existing script already supports `--user` parameter
- Just need to call it with the current user's ID

## User Flow

```
1. User selects themselves in UserSelector
2. User navigates to "Tablet" tab
3. User sees: "Sync database for [User Name]"
4. User clicks "Sync My Database"
5. Progress shows: "Syncing plans for [User Name]..."
6. Success: "Synced 5 plans, 120 steps for [User Name]"
7. Database updated (only this user's data)
```

## Technical Details

### Tauri Command Signature
```rust
#[tauri::command]
async fn sync_tablet_db(
    user_id: String,           // Current user's ID
    include_existing: bool,     // Update existing plans?
    plan_limit: i32,           // Max plans to fetch
    timeout: f64,              // API timeout
) -> Result<SyncResult, String>
```

### Python Script Call
```bash
python scripts/sync_browser_plans_to_tablet_db.py \
  --user <current_user_id> \
  --include-existing \
  --plan-limit 20 \
  --timeout 120 \
  --db-path data/lesson_planner.db
```

### Frontend Component State
```typescript
const { currentUser } = useStore();  // Get current user
const [isSyncing, setIsSyncing] = useState(false);
const [syncProgress, setSyncProgress] = useState('');
const [syncResult, setSyncResult] = useState(null);
```

## Security

- ✅ Only syncs current user's data (user_id validated in Tauri command)
- ✅ Backend API already enforces user access via `X-Current-User-Id` header
- ✅ Database backup created automatically before sync
- ✅ Input validation (plan_limit, timeout are sanitized)

## Files to Create/Modify

### New Files
- `frontend/src/components/TabletSync.tsx` - Main component
- (If using sidecar IPC) Rust+Python changes in the existing sidecar plumbing
- (If using backend endpoint) no new Rust files required

### Modified Files
- `frontend/src/components/desktop/DesktopNav.tsx` - Add "tablet" nav item
- `frontend/src/components/layouts/DesktopLayout.tsx` - Update NavItem type
- `lesson-plan-browser/frontend/src/App.tsx` - Add "tablet" case to switch (this is the real unified app used by PC)
- (If using backend endpoint) `backend/api.py` - Add `POST /api/tablet/sync`

### Unchanged Files
- `scripts/sync_browser_plans_to_tablet_db.py` - No changes needed
- `sync-database-to-tablet.ps1` - Still works for admin/all-users sync
- `build-apk.ps1` - No changes needed
- `install-apk.ps1` - No changes needed

## Benefits

1. **User Isolation**: Each user only updates their own data
2. **Ease of Use**: No need to manually specify user ID
3. **Real-time Feedback**: Progress visible in UI
4. **Error Handling**: User-friendly error messages
5. **Backward Compatible**: Existing scripts still work for admin use

## Next Steps

1. Review and approve plan
2. Implement Phase 1 (Navigation)
3. Implement Phase 2 (Component UI)
4. Implement Phase 3 (Tauri Command)
5. Implement Phase 4 (Integration)
6. Test and refine

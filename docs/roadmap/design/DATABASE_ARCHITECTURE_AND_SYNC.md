# Database Architecture and Synchronization Strategy

## Executive Summary

This document outlines the database architecture and synchronization strategy for the Lesson Plan Builder application, supporting two teachers with local-first navigation and efficient peer-to-peer (P2P) synchronization between PC and Android tablet, with Supabase as cloud backup.

> **Reality check (Dec 2025):**  
> - ✅ **Partially Implemented**: The `lesson_json` column DOES exist in `WeeklyPlan` (stored as TEXT in SQLite, but handled as dict in Python). `OriginalLessonPlan` is also fully implemented.
> - ⚠️ **Sync Gaps**: `sync_status`, `last_synced_at`, and `vector_vector` columns are **MISSING**. The code currently has no concept of synchronization state.
> - ❌ **Missing Tables**: `rag_retrievals`, `file_search_documents`, and local cache tables do not exist.
> - ❌ **No Supabase**: `settings.USE_SUPABASE` defaults to false, and no Supabase client is active in `backend/database.py`.

**Key Features:**
- **Local-first architecture**: Fast navigation using local cache
- **P2P synchronization**: Direct device-to-device sync (minimal bandwidth)
- **Cloud backup**: Supabase stores complete lesson plans for backup/offline scenarios
- **Free tier compatible**: 2 Supabase projects (one per teacher) within free tier limits

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PC (Primary Creator)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Cache (SQLite/JSON files)                     │   │
│  │  - Complete lesson plans                             │   │
│  │  - Fast local queries                                │   │
│  │  - Offline navigation                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                    ↕ P2P Sync (WiFi/Bluetooth)              │
│                    ↕ Cloud Backup (Supabase)                │
└─────────────────────────────────────────────────────────────┘
                        ↕ Direct Sync
┌─────────────────────────────────────────────────────────────┐
│              Android Tablet (Navigator/Editor)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Cache (SQLite/Realm)                          │   │
│  │  - Complete lesson plans                             │   │
│  │  - Fast local queries                                │   │
│  │  - Offline navigation                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                    ↕ P2P Sync (WiFi/Bluetooth)              │
│                    ↕ Cloud Backup (Supabase)                │
└─────────────────────────────────────────────────────────────┘
                        ↕ Backup Sync
┌─────────────────────────────────────────────────────────────┐
│              Supabase (Cloud Backup)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Project 1 (Teacher 1)                               │   │
│  │  - lesson_json JSONB column                          │   │
│  │  - 500MB capacity                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Project 2 (Teacher 2)                               │   │
│  │  - lesson_json JSONB column                          │   │
│  │  - 500MB capacity                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Supabase Schema Changes

**Add JSONB column to `weekly_plans` table (**not yet implemented**):**

```sql
-- Migration: Add lesson_json JSONB column
ALTER TABLE weekly_plans 
ADD COLUMN lesson_json JSONB;

-- Add index for fast JSON queries
CREATE INDEX idx_weekly_plans_lesson_json_metadata 
ON weekly_plans 
USING GIN ((lesson_json->'metadata'));

-- Add index for day-level queries
CREATE INDEX idx_weekly_plans_lesson_json_days 
ON weekly_plans 
USING GIN ((lesson_json->'days'));

-- Add index for sync operations (modified_at)
CREATE INDEX idx_weekly_plans_sync 
ON weekly_plans (user_id, updated_at);

-- Add column to track sync status
ALTER TABLE weekly_plans 
ADD COLUMN sync_status TEXT DEFAULT 'pending',
ADD COLUMN last_synced_at TIMESTAMP,
ADD COLUMN sync_device_id TEXT;
```

**Schema Structure:**

```sql
CREATE TABLE weekly_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    week_folder_path TEXT,
    output_file TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    
    -- Existing performance metrics
    processing_time_ms REAL,
    total_tokens INTEGER,
    total_cost_usd REAL,
    llm_model TEXT,
    
    -- NEW: Lesson plan JSON storage
    lesson_json JSONB,  -- Complete lesson plan JSON
    
    -- NEW: Sync tracking
    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'synced', 'conflict'
    last_synced_at TIMESTAMP,
    sync_device_id TEXT,  -- Which device last synced
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Local Cache Schema (PC - SQLite) – **not yet implemented**

```sql
CREATE TABLE local_lesson_plans (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    slot_number INTEGER,
    lesson_json TEXT NOT NULL,  -- JSON string
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    sync_status TEXT DEFAULT 'pending',  -- 'pending', 'synced', 'conflict'
    device_id TEXT,  -- 'pc' or 'tablet'
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_local_plans_sync 
ON local_lesson_plans (user_id, modified_at, sync_status);

CREATE INDEX idx_local_plans_week 
ON local_lesson_plans (user_id, week_of, slot_number);
```

### Local Cache Schema (Android - SQLite/Room) – **not yet implemented**

```kotlin
@Entity(tableName = "local_lesson_plans")
data class LocalLessonPlan(
    @PrimaryKey val id: String,
    val userId: String,
    val weekOf: String,
    val slotNumber: Int?,
    val lessonJson: String,  // JSON string
    val modifiedAt: Long,  // Timestamp
    val syncedAt: Long?,
    val syncStatus: String = "pending",  // 'pending', 'synced', 'conflict'
    val deviceId: String = "tablet",
    val version: Int = 1
)

@Dao
interface LessonPlanDao {
    @Query("SELECT * FROM local_lesson_plans WHERE userId = :userId AND syncStatus = 'pending' ORDER BY modifiedAt")
    fun getPendingSyncs(userId: String): List<LocalLessonPlan>
    
    @Query("SELECT * FROM local_lesson_plans WHERE userId = :userId AND weekOf = :weekOf AND slotNumber = :slotNumber")
    fun getLessonPlan(userId: String, weekOf: String, slotNumber: Int): LocalLessonPlan?
}
```

## Storage Capacity Analysis

### Per Teacher Storage

**Single lesson plan (one slot, 5 days):**
- JSON size: ~20-50KB
- With compression: ~10-15KB

**Full week (5 slots):**
- JSON size: ~100-250KB
- With compression: ~50-125KB

**Per year (40 weeks, 5 slots/week):**
- Uncompressed: ~10-20MB
- Compressed: ~5-10MB
- With metadata/indices: ~15-20MB

**Multiple years:**
- 5 years: ~75-100MB
- 10 years: ~150-200MB
- 25 years: ~375-500MB (approaching limit)

### Free Tier Sufficiency

**Supabase Free Tier:**
- Database storage: 500MB per project
- 2 projects (one per teacher) = 1GB total
- Each teacher: ~20MB/year
- **Capacity: ~25 years per teacher** ✅

**Conclusion:** Free tier is sufficient for long-term use.

## Synchronization Strategy

### Sync Flow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Sync Priority                             │
│  1. P2P Sync (Primary) - Direct device-to-device            │
│  2. Cloud Backup (Secondary) - Supabase backup              │
│  3. Conflict Resolution - When devices diverge              │
└─────────────────────────────────────────────────────────────┘
```

### Scenario 1: Normal Operation (Devices Together)

**Flow:**
1. PC creates/edits lesson plan → saves to local cache
2. PC detects tablet on local network (mDNS/Bonjour)
3. PC syncs directly to tablet (WiFi/Bluetooth)
4. Both devices sync to Supabase in background (backup)

**Benefits:**
- Fast sync (local network: 10-100x faster)
- No internet required
- Minimal bandwidth usage

### Scenario 2: Tablet Makes Edits During Week

**Flow:**
1. Tablet edits lesson plan → saves to local cache
2. Tablet detects PC on local network
3. Tablet syncs changes to PC directly
4. PC syncs to Supabase (backup)

**Benefits:**
- Real-time collaboration
- Fast local sync
- Cloud backup for safety

### Scenario 3: Devices Apart (Cloud Fallback)

**Flow:**
1. PC creates/edits → saves locally
2. PC syncs to Supabase (cloud backup)
3. Tablet syncs from Supabase when online
4. When devices reconnect → P2P sync reconciles

**Benefits:**
- Works when devices are apart
- Cloud backup ensures data safety
- Automatic reconciliation on reconnect

## P2P Synchronization Protocol

### Device Discovery

**PC Side (Python):**
```python
from zeroconf import ServiceInfo, Zeroconf
import socket

class DeviceDiscovery:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.service_type = "_lessonplan._tcp.local."
        self.service_name = "LessonPlan-PC.local."
    
    def advertise_pc(self, port=8080):
        """Advertise PC availability for sync"""
        info = ServiceInfo(
            self.service_type,
            self.service_name,
            addresses=[socket.inet_aton(self.get_local_ip())],
            port=port,
            properties={'device': 'pc', 'version': '1.0'}
        )
        self.zeroconf.register_service(info)
    
    def discover_tablet(self):
        """Discover tablet on local network"""
        browser = ServiceBrowser(self.zeroconf, self.service_type, self)
        # Returns tablet IP and port when found
```

**Android Side (Kotlin):**
```kotlin
class DeviceDiscovery(private val context: Context) {
    private val nsdManager = context.getSystemService(Context.NSD_SERVICE) as NsdManager
    private val serviceType = "_lessonplan._tcp"
    private val serviceName = "LessonPlan-Tablet"
    
    fun advertiseTablet(port: Int) {
        val serviceInfo = NsdServiceInfo().apply {
            setServiceName(serviceName)
            setServiceType(serviceType)
            setPort(port)
        }
        nsdManager.registerService(serviceInfo, NsdManager.PROTOCOL_DNS_SD, registrationListener)
    }
    
    fun discoverPC() {
        nsdManager.discoverServices(serviceType, NsdManager.PROTOCOL_DNS_SD, discoveryListener)
    }
}
```

### Sync Protocol

**Delta Sync (Only Changes):**
```json
{
  "sync_type": "delta",
  "device_id": "pc",
  "plan_id": "abc123",
  "modified_fields": {
    "days.monday.objective.student_goal": "New goal",
    "days.tuesday.assessment.primary_assessment": "Updated assessment"
  },
  "modified_at": "2025-01-15T10:30:00Z",
  "version": 2
}
```

**Full Sync (When Needed):**
```json
{
  "sync_type": "full",
  "device_id": "pc",
  "plan_id": "abc123",
  "lesson_json": { /* complete lesson plan */ },
  "modified_at": "2025-01-15T10:30:00Z",
  "version": 1
}
```

**Sync Request:**
```json
{
  "action": "sync_request",
  "device_id": "tablet",
  "last_sync_time": "2025-01-14T08:00:00Z",
  "pending_plans": ["plan1", "plan2"]
}
```

### P2P Sync Implementation

**PC Side (Python):**
```python
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/sync', methods=['POST'])
def sync_from_tablet():
    """Receive sync from tablet"""
    data = request.json
    plan_id = data['plan_id']
    lesson_json = data['lesson_json']
    
    # Save to local cache
    local_cache.save(plan_id, lesson_json)
    
    # Update sync status
    local_cache.update_sync_status(plan_id, 'synced')
    
    # Background sync to Supabase
    supabase_backup(plan_id, lesson_json)
    
    return jsonify({'status': 'success'})

def sync_to_tablet(tablet_ip, plan_id, lesson_json):
    """Send sync to tablet"""
    import requests
    
    url = f"http://{tablet_ip}:8080/sync"
    payload = {
        'plan_id': plan_id,
        'lesson_json': lesson_json,
        'device_id': 'pc',
        'sync_type': 'full'
    }
    
    response = requests.post(url, json=payload)
    return response.json()
```

**Android Side (Kotlin):**
```kotlin
class P2PSyncService(private val context: Context) {
    private val httpServer = HttpServer(8080)
    
    fun startServer() {
        httpServer.onRequest("/sync") { request ->
            val planId = request.json.getString("plan_id")
            val lessonJson = request.json.getString("lesson_json")
            
            // Save to local cache
            localDb.saveLessonPlan(planId, lessonJson)
            
            // Update sync status
            localDb.updateSyncStatus(planId, "synced")
            
            // Background sync to Supabase
            supabaseBackup(planId, lessonJson)
            
            JsonResponse(200, mapOf("status" to "success"))
        }
    }
    
    suspend fun syncToPC(pcIp: String, planId: String, lessonJson: String) {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("http://$pcIp:8080/sync")
            .post(RequestBody.create(
                MediaType.parse("application/json"),
                json {
                    "plan_id" to planId
                    "lesson_json" to lessonJson
                    "device_id" to "tablet"
                    "sync_type" to "full"
                }.toString()
            ))
            .build()
        
        client.newCall(request).execute()
    }
}
```

## Cloud Backup Strategy

### Supabase Backup Flow

**When to Backup:**
1. After P2P sync completes
2. Periodically (every hour) for pending changes
3. On app close/background
4. When device goes offline

**Backup Implementation:**

**PC Side (Python):**
```python
def supabase_backup(plan_id, lesson_json):
    """Backup lesson plan to Supabase"""
    try:
        # Update weekly_plans table with lesson_json
        supabase.table("weekly_plans").update({
            "lesson_json": lesson_json,
            "sync_status": "synced",
            "last_synced_at": datetime.now().isoformat(),
            "sync_device_id": "pc"
        }).eq("id", plan_id).execute()
        
        logger.info("supabase_backup_success", extra={"plan_id": plan_id})
    except Exception as e:
        logger.error("supabase_backup_failed", extra={"plan_id": plan_id, "error": str(e)})
        # Retry logic
        retry_backup(plan_id, lesson_json)

def sync_from_supabase(user_id, last_sync_time=None):
    """Sync lesson plans from Supabase (when devices apart)"""
    query = supabase.table("weekly_plans").select("*").eq("user_id", user_id)
    
    if last_sync_time:
        query = query.gte("updated_at", last_sync_time.isoformat())
    
    plans = query.execute()
    
    for plan in plans.data:
        if plan.get("lesson_json"):
            local_cache.save(plan["id"], plan["lesson_json"])
```

**Android Side (Kotlin):**
```kotlin
suspend fun supabaseBackup(planId: String, lessonJson: String) {
    try {
        supabase.from("weekly_plans")
            .update(mapOf(
                "lesson_json" to Json.parseToJsonElement(lessonJson),
                "sync_status" to "synced",
                "last_synced_at" to Instant.now().toString(),
                "sync_device_id" to "tablet"
            ))
            .eq("id", planId)
            .execute()
    } catch (e: Exception) {
        Log.e("Sync", "Supabase backup failed", e)
        // Retry logic
        retryBackup(planId, lessonJson)
    }
}

suspend fun syncFromSupabase(userId: String, lastSyncTime: Instant? = null) {
    var query = supabase.from("weekly_plans")
        .select("*")
        .eq("user_id", userId)
    
    if (lastSyncTime != null) {
        query = query.gte("updated_at", lastSyncTime.toString())
    }
    
    val plans = query.execute()
    
    plans.forEach { plan ->
        plan.lessonJson?.let { json ->
            localDb.saveLessonPlan(plan.id, json.toString())
        }
    }
}
```

## Conflict Resolution

### Conflict Detection

**When conflicts occur:**
- Both devices edit the same plan independently
- Devices are apart, then reconnect
- Network issues during sync

**Enhanced Conflict Detection with Field-Level Analysis:**
```python
def detect_conflict(local_plan, remote_plan):
    """Detect conflicts at field level using JSON path tracking."""
    local_version = local_plan.get('version', 1)
    remote_version = remote_plan.get('version', 1)
    local_modified = local_plan.get('modified_at')
    remote_modified = remote_plan.get('modified_at')
    
    # No conflict if versions match
    if local_version == remote_version:
        return False, []
    
    # Both modified - check field-level conflicts
    if local_modified and remote_modified:
        conflicting_fields = find_conflicting_fields(
            local_plan.get('lesson_json', {}),
            remote_plan.get('lesson_json', {})
        )
        return len(conflicting_fields) > 0, conflicting_fields
    
    return False, []

def find_conflicting_fields(local_json: dict, remote_json: dict) -> list:
    """Find fields that were modified in both versions."""
    local_changes = get_modified_fields(local_json)
    remote_changes = get_modified_fields(remote_json)
    
    # Find intersection (fields modified in both)
    conflicting = []
    for field_path in local_changes:
        if field_path in remote_changes:
            local_value = get_json_path(local_json, field_path)
            remote_value = get_json_path(remote_json, field_path)
            
            # Only conflict if values actually differ
            if local_value != remote_value:
                conflicting.append({
                    'path': field_path,
                    'local_value': local_value,
                    'remote_value': remote_value
                })
    
    return conflicting
```

**Vector Clock Implementation** (Enhanced Version Tracking):
```sql
-- Enhanced version tracking with vector clocks
ALTER TABLE weekly_plans 
ADD COLUMN version_vector JSONB DEFAULT '{}';

-- Example: {"pc": 5, "tablet": 3}
-- PC has seen tablet's version 3, tablet has seen PC's version 5
-- When PC updates, increment pc to 6: {"pc": 6, "tablet": 3}
```

```python
def compare_vector_clocks(local_vc: dict, remote_vc: dict) -> str:
    """
    Compare vector clocks to determine relationship.
    Returns: 'before', 'after', 'concurrent', or 'equal'
    """
    local_ahead = any(
        local_vc.get(device, 0) > remote_vc.get(device, 0)
        for device in local_vc
    )
    remote_ahead = any(
        remote_vc.get(device, 0) > local_vc.get(device, 0)
        for device in remote_vc
    )
    
    if local_ahead and remote_ahead:
        return 'concurrent'  # Conflict
    elif local_ahead:
        return 'after'  # Local is newer
    elif remote_ahead:
        return 'before'  # Remote is newer
    else:
        return 'equal'  # Same version
```

### Resolution Strategies

**Strategy 1: Last-Write-Wins (Recommended)**
```python
def resolve_conflict_last_write_wins(local_plan, remote_plan):
    """Use most recent modification"""
    local_time = parse_timestamp(local_plan['modified_at'])
    remote_time = parse_timestamp(remote_plan['modified_at'])
    
    if local_time > remote_time:
        return local_plan  # Local wins
    else:
        return remote_plan  # Remote wins
```

**Strategy 2: Field-Level Merge (Enhanced)**
```python
def resolve_conflict_merge(local_plan, remote_plan, conflicting_fields: list):
    """Merge changes at field level, only conflicting fields need resolution."""
    merged = local_plan.copy()
    merged_json = merged.get('lesson_json', {})
    remote_json = remote_plan.get('lesson_json', {})
    
    # Automatically merge non-conflicting fields
    local_changes = get_modified_fields(local_json)
    remote_changes = get_modified_fields(remote_json)
    
    conflicting_paths = {cf['path'] for cf in conflicting_fields}
    
    # Apply non-conflicting remote changes
    for field_path in remote_changes:
        if field_path not in conflicting_paths:
            # Safe to merge - field only modified remotely
            remote_value = get_json_path(remote_json, field_path)
            set_json_path(merged_json, field_path, remote_value)
    
    # Keep local values for conflicting fields (or apply merge logic)
    for conflict in conflicting_fields:
        field_path = conflict['path']
        # For now, keep local value (could apply 3-way merge with base)
        # Future: Implement 3-way merge with common ancestor
        local_value = conflict['local_value']
        set_json_path(merged_json, field_path, local_value)
    
    merged['lesson_json'] = merged_json
    merged['conflict_resolution'] = {
        'strategy': 'field_level_merge',
        'conflicting_fields': conflicting_fields,
        'auto_merged_fields': list(remote_changes - conflicting_paths)
    }
    
    return merged
```

**JSON Patch-Based Conflict Resolution**:
```python
def apply_json_patch_with_conflict_detection(base: dict, patch: list) -> dict:
    """Apply JSON patch, detecting conflicts."""
    result = base.copy()
    conflicts = []
    
    for operation in patch:
        op = operation['op']
        path = operation['path']
        value = operation.get('value')
        
        if op == 'replace':
            current_value = get_json_path(result, path)
            if current_value != operation.get('old_value'):
                # Conflict: value changed since patch was created
                conflicts.append({
                    'path': path,
                    'operation': op,
                    'expected': operation.get('old_value'),
                    'actual': current_value,
                    'new_value': value
                })
            else:
                # Safe to apply
                set_json_path(result, path, value)
        # ... handle other operations (add, remove, etc.)
    
    return result, conflicts
```

**Strategy 3: Manual Resolution**
```python
def resolve_conflict_manual(local_plan, remote_plan):
    """Flag for manual resolution"""
    # Mark as conflict
    local_cache.update_sync_status(plan_id, 'conflict')
    
    # Store both versions
    local_cache.save_conflict_version(plan_id, 'local', local_plan)
    local_cache.save_conflict_version(plan_id, 'remote', remote_plan)
    
    # Notify user to resolve manually
    notify_user_conflict(plan_id)
```

## Sync Status Tracking

### Sync States

- **pending**: Changes made, not yet synced
- **syncing**: Currently syncing
- **synced**: Successfully synced
- **conflict**: Conflict detected, needs resolution
- **failed**: Sync failed, needs retry

### Status Management

```python
class SyncStatus:
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"

def update_sync_status(plan_id, status, device_id=None):
    """Update sync status"""
    local_cache.update_sync_status(plan_id, status)
    
    if status == SyncStatus.SYNCED:
        local_cache.update_synced_at(plan_id, datetime.now())
        if device_id:
            local_cache.update_device_id(plan_id, device_id)
```

## Implementation Phases

### Phase 1: Database Schema (Week 1)
- [ ] Add `lesson_json` JSONB column to Supabase
- [ ] Add sync tracking columns
- [ ] Create indexes for JSON queries
- [ ] Update local cache schemas (PC and Android)

### Phase 2: Local Caching (Week 2)
- [ ] Implement local cache on PC (SQLite)
- [ ] Implement local cache on Android (SQLite/Room)
- [ ] Add cache management (save, retrieve, update)
- [ ] Add cache invalidation logic

### Phase 3: P2P Sync (Week 3-4)
- [ ] Implement device discovery (mDNS/Bonjour)
- [ ] Implement P2P sync protocol
- [ ] Add delta sync support
- [ ] Add conflict detection

### Phase 4: Cloud Backup (Week 5)
- [ ] Implement Supabase backup
- [ ] Add background sync
- [ ] Add retry logic
- [ ] Add sync status tracking

### Phase 5: Conflict Resolution (Week 6)
- [ ] Implement conflict detection
- [ ] Add resolution strategies
- [ ] Add manual resolution UI
- [ ] Test conflict scenarios

### Phase 6: Testing & Optimization (Week 7-8)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Error handling
- [ ] Documentation

## Performance Considerations

### Local Cache Performance
- **Query speed**: < 10ms (local SQLite)
- **Storage**: Efficient JSON storage
- **Indexing**: Index on user_id, week_of, slot_number

### P2P Sync Performance
- **Discovery**: < 2 seconds (mDNS)
- **Sync speed**: 10-100MB/s (local network)
- **Latency**: < 50ms (local network)

### Cloud Backup Performance
- **Upload**: ~1-5 seconds per plan (depends on size)
- **Download**: ~1-3 seconds per plan
- **Bandwidth**: Minimal (only when needed)

## Security Considerations

### P2P Sync Security

**CRITICAL**: P2P sync security must be implemented before deployment. Without proper security, the sync system is vulnerable to man-in-the-middle attacks and unauthorized access.

#### Device Pairing Protocol

**Initial Pairing Process**:
1. **Discovery**: Devices advertise availability via mDNS/Bonjour with device fingerprint
2. **Pairing Initiation**: User initiates pairing via QR code scan or manual code entry
3. **Key Exchange**: 
   - Generate Ed25519 key pair on each device (lightweight, fast)
   - Exchange public keys over secure channel (QR code or manual entry)
   - Store paired device public key in secure storage (OS keychain)
4. **Certificate Generation**: 
   - Create self-signed certificate for each device
   - Certificate includes device ID, user ID, and public key
   - Certificate signed by user's master key (stored in OS keychain)
5. **Pairing Timeout**: 5-minute window for initial handshake (prevents replay attacks)

**Pairing Code Format**:
```
LP-XXXX-YYYY-ZZZZ
- XXXX: Device type (PC01, TAB1)
- YYYY: User ID hash (first 4 chars)
- ZZZZ: Random pairing code
```

#### Encryption Implementation

**Transport Layer**:
- **Protocol**: TLS 1.3 minimum (perfect forward secrecy required)
- **Cipher Suites**: TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256
- **Mutual Authentication**: Both devices must present valid certificates
- **Certificate Pinning**: Pin device certificates to prevent MITM attacks

**Data at Rest**:
- **Algorithm**: AES-256-GCM (authenticated encryption)
- **Key Derivation**: PBKDF2 with 100,000 iterations, SHA-256
- **Key Storage**: OS keychain (Windows Credential Manager, macOS Keychain, Android Keystore)
- **IV Generation**: Cryptographically secure random IV per encryption operation

**Key Management**:
```python
# backend/services/p2p_security.py
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class P2PSecurity:
    def __init__(self):
        self.device_key = self._load_or_generate_device_key()
        self.paired_devices = self._load_paired_devices()
    
    def generate_pairing_code(self) -> str:
        """Generate secure pairing code."""
        random_bytes = os.urandom(4)
        code = ''.join(f'{b:02X}' for b in random_bytes)
        return f"LP-{self.device_id[:4]}-{code}"
    
    def pair_device(self, pairing_code: str, remote_public_key: bytes):
        """Pair with remote device using pairing code."""
        # Verify pairing code
        # Exchange and verify certificates
        # Store paired device certificate
        pass
    
    def encrypt_sync_data(self, data: bytes, target_device_id: str) -> bytes:
        """Encrypt data for specific paired device."""
        # Derive shared secret
        # Encrypt with AES-256-GCM
        # Return encrypted data + IV + tag
        pass
```

#### Threat Model

**Threats Addressed**:
1. **Man-in-the-Middle Attacks**: Prevented by certificate pinning and mutual TLS
2. **Replay Attacks**: Prevented by nonces and timestamps in sync protocol
3. **Unauthorized Device Access**: Prevented by device pairing requirement
4. **Data Interception**: Prevented by TLS 1.3 encryption
5. **Key Compromise**: Mitigated by perfect forward secrecy (TLS 1.3)

**Security Assumptions**:
- OS keychain is secure (reasonable for desktop/mobile apps)
- Network is untrusted (assume public WiFi)
- Physical device security is user's responsibility

#### Validation and Identity Verification

**Device Identity Verification**:
- Each device has unique device ID (generated on first install)
- Device ID stored in secure storage, cannot be changed
- Certificate includes device ID and user ID
- Certificate revocation list (CRL) stored in Supabase (check on each sync)

**Sync Request Validation**:
```python
def validate_sync_request(request: SyncRequest) -> bool:
    """Validate incoming sync request."""
    # 1. Verify device is paired
    if not is_device_paired(request.device_id):
        return False
    
    # 2. Verify certificate
    if not verify_certificate(request.certificate):
        return False
    
    # 3. Check certificate revocation
    if is_certificate_revoked(request.certificate):
        return False
    
    # 4. Verify signature
    if not verify_signature(request.data, request.signature, request.public_key):
        return False
    
    # 5. Check timestamp (prevent replay)
    if is_timestamp_stale(request.timestamp):
        return False
    
    return True
```

### Cloud Backup Security
- **Authentication**: Supabase Row Level Security (RLS)
- **Encryption**: Supabase encryption at rest
- **Access Control**: User-specific data isolation

**RLS Policies**:
```sql
-- Ensure users can only access their own data
CREATE POLICY "Users can only access own lesson plans"
ON weekly_plans FOR ALL
USING (auth.uid() = user_id);

CREATE POLICY "Users can only access own vocabulary approvals"
ON vocabulary_teacher_approvals FOR ALL
USING (auth.uid() = user_id);
```

## Error Handling

### Sync Failures
- **Retry logic**: Exponential backoff
- **Queue management**: Queue failed syncs
- **Notification**: Alert user of sync failures

### Network Issues
- **Offline mode**: Continue working offline
- **Queue syncs**: Queue when offline, sync when online
- **Conflict handling**: Detect conflicts on reconnect

## Monitoring & Logging

### Sync Metrics
- Sync success rate
- Sync duration
- Conflict frequency
- Bandwidth usage

### Logging
- Sync events (start, success, failure)
- Conflict detection
- Performance metrics
- Error details

## Conclusion

This architecture provides:
- ✅ **Fast local navigation** (local cache)
- ✅ **Efficient sync** (P2P + cloud backup)
- ✅ **Free tier compatible** (2 projects, 500MB each)
- ✅ **Offline capability** (local-first)
- ✅ **Data safety** (cloud backup)

The hybrid approach (P2P + cloud backup) minimizes bandwidth usage while ensuring data availability and safety.

---

## References

- [README.md](./README.md) - Master index of all expansion documents
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) - Enhanced generation architecture
- [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md) - Docker/Kubernetes recommendations


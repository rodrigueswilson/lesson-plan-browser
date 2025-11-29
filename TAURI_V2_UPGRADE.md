# Tauri v2.0 Upgrade Guide

## Changes Required

### 1. Dependencies Updated ✅
- `Cargo.toml`: Updated to Tauri v2.0 and plugins
- `package.json`: Updated to @tauri-apps/cli v2.0

### 2. Code Changes Needed

#### Rust (main.rs)
- Remove `tauri::api::dialog` (use plugin instead)
- Update plugin registration
- Commands should work mostly the same

#### Frontend (api.ts)
- Update imports: `@tauri-apps/api/tauri` → `@tauri-apps/api/core`
- Update HTTP imports if needed

#### Configuration (tauri.conf.json)
- Convert to v2 format (different structure)
- Use `plugins` instead of `allowlist`
- Update permissions model

### 3. Migration Steps

1. ✅ Update dependencies
2. ⏳ Update Rust code (remove old APIs)
3. ⏳ Update tauri.conf.json to v2 format
4. ⏳ Update frontend API imports
5. ⏳ Test desktop functionality
6. ⏳ Initialize Android project


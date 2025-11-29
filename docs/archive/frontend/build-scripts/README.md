# Deprecated Build Scripts Reference

This directory contains references to deprecated build scripts that have been archived elsewhere.

## Archive Location

Deprecated build scripts are archived in:
**`lesson-plan-browser/scripts/archive/deprecated-build-scripts/`**

## Archived Scripts

The following scripts have been archived and are no longer in active use:

- `build-android.ps1`
- `build-pc.ps1`
- `frontend_build-tablet.ps1`
- `install-android-app.ps1`
- `root_build-android-offline.ps1`
- `root_check-install-status.ps1`
- `root_fresh-install.ps1`
- `root_install-android-app.ps1`
- `root_rebuild-and-fresh-install.ps1`
- `root_rebuild-android.ps1`
- `scripts_tablet_build.py`

## Current Canonical Build Scripts

**Android Build:**
- Entry point: `lesson-plan-browser/scripts/run-with-ndk.ps1`
- Main builder: `lesson-plan-browser/scripts/build-android-offline.ps1`

**PC Build:**
- Development: `npm run tauri:dev` in `frontend/`
- Production: `npm run tauri:build` in `frontend/`

## Archive Date

These scripts were archived on **November 29, 2025** when the canonical build scripts were established.

## Reference

See `lesson-plan-browser/README.md` for current build instructions.

---

**Document Status**: Reference Only  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team


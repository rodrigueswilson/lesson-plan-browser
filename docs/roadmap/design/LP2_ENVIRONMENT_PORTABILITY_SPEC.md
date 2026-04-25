# LP2 Environment Portability Spec

Status: Draft specification
Last updated: 2026-04-23

## Objective
Define a portable, repeatable environment model for LP2 that is easy to move across machines and safe for local-first workflows.

## Environment Model

### Host Responsibilities
- Run Tauri desktop UI.
- Store user-local secrets in OS keychain or local secret store.
- Provide Docker runtime for service plane.

### Container Responsibilities
- Backend API runtime.
- Optional retrieval/vector runtime.
- Optional worker runtimes for heavy background tasks.
- Optional relational database service (for LP2 experiments).

## Configuration Contract
- Commit `.env.example` with non-secret defaults and required variable keys.
- Never commit live secrets.
- Split variables into:
  - app runtime config,
  - infrastructure config,
  - secret references.

## Data and Storage Policy
- Use named volumes for persistent container data.
- Use bind mounts only where source sync is required.
- Maintain explicit backup path and retention policy.
- Define restore procedure and verify with periodic drills.

## Health and Startup Policy
- Every stateful service exposes a health check.
- Service dependencies use readiness semantics, not only start order.
- Startup failures must produce actionable logs.

## Machine Migration Checklist
1. Install runtime prerequisites (Docker, language runtimes if needed for host UI).
2. Copy or restore required named volume data.
3. Populate `.env` from approved template and secure secret sources.
4. Launch service profile and verify health.
5. Run smoke tests for core flows.
6. Validate backup and restore command path on new machine.

## Portability Acceptance Criteria
- Fresh machine setup to healthy stack within target time window.
- No undocumented manual steps required for critical paths.
- Backup restore returns app to usable state.
- Core lesson flow works consistently across at least two machine profiles.

## Security and Compliance Notes
- Keep PII out embedding/index payloads unless explicitly approved.
- Encrypt backup artifacts when stored outside local trusted path.
- Document data handling boundaries for any cloud-integrated option.

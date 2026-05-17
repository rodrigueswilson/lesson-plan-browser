# Architecture Gate Risk Register

Status: Draft
Last updated: 2026-04-23

## Scale
- Probability: Low / Medium / High
- Impact: Low / Medium / High
- Residual risk: expected risk after mitigation

## Risks

| ID | Risk | Probability | Impact | Mitigation | Residual |
|---|---|---|---|---|---|
| R1 | Migration scope underestimated for MariaDB-primary path | Medium | High | Timebox discovery spike; require schema + sync + rollback design before commitment | Medium |
| R2 | Retrieval quality regressions from embedding/model changes | Medium | High | Freeze benchmark query sets; version-lock embedding model during gate cycle; add relevance regression checks | Medium |
| R3 | Model lifecycle drift (preview/GA changes, deprecations) | Medium | Medium | Track model lifecycle pages monthly; keep provider abstraction; document fallback model | Low-Medium |
| R4 | Cost variance from embedding token volume | Medium | Medium | Add token-budget forecast and cost guardrails; test multiple dimensions | Medium |
| R5 | Metadata filter bypass causes cross-grade leakage | Low-Medium | High | Hard gate constraints on leakage; strict metadata prefilter before similarity search | Low |
| R6 | Operational burden increases (backups, monitoring, patching) | Medium | Medium-High | Define operational runbook and ownership before go-live; include restore drills in benchmark | Medium |
| R7 | Sync architecture drift from current SQLite/Supabase assumptions | High (if MariaDB-primary) | High | Keep `retrieve_context` and data-domain boundaries; isolate retrieval pilot before core migration | Medium |
| R8 | Vendor lock-in due to engine-specific vector features | Medium | Medium | Use provider interface and compatibility tests; avoid embedding engine-specific logic in business layer | Low-Medium |
| R9 | Security/compliance gap for educational data handling | Low-Medium | High | Maintain existing data-minimization patterns; keep PII out embedding pipeline; audit logs for retrieval | Low |
| R10 | Team learning curve delays delivery | Medium | Medium | Narrow initial scope to pilot; provide runbook + pair reviews + staged rollout | Low-Medium |

## Gate-Blocking Risks
The following must be reduced before a Go decision:
- R1 migration uncertainty (must have validated phased migration and rollback).
- R5 cross-grade leakage (must meet hard benchmark limits).
- R7 sync architecture drift (must not break local-first and current operational requirements).

## Monitoring Signals
- Weekly: retrieval leakage rate, p95 retrieval latency, embedding spend trend.
- Monthly: model lifecycle status, DB version security updates.
- Per release: restore drill success and migration rehearsal status.

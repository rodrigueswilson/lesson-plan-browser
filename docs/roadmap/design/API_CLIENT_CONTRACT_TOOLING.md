# API client contract tooling (frontend–backend HTTP)

**Status:** Planning (recommended approach; not implemented)  
**Updated:** 2026-03-22  
**Purpose:** Define how the TypeScript/React side should stay aligned with the FastAPI OpenAPI schema, improve reviewability, and reduce duplicated URL and type logic—without replacing the backend stack.

---

## Context in this repository

| Layer | Role today |
| ----- | ---------- |
| **Backend** | [FastAPI](../../../backend/api.py) serves REST and related behavior under `/api` (routers mounted with `prefix="/api"`). Interactive docs: `/api/docs`. The authoritative description of request/response shapes for HTTP is the **OpenAPI document** FastAPI generates from route signatures and Pydantic models. |
| **Frontend** | React with **TanStack React Query** already in use ([frontend/package.json](../../../frontend/package.json)). Much networking is centralized in [shared/lesson-api/src/index.ts](../../../shared/lesson-api/src/index.ts) via `fetch`, while some components still use **hardcoded** base URLs (e.g. `http://localhost:8000/api`), which duplicates the SSOT for “where the API lives.” |
| **Curriculum router** | [backend/routers/curriculum.py](../../../backend/routers/curriculum.py) uses **Pydantic response models** in [backend/schemas/curriculum.py](../../../backend/schemas/curriculum.py) so OpenAPI documents lesson detail fields (including `standards_structured`), search hits, and gap payloads—suitable for an **Orval** slice before migrating ad hoc `fetch` in lesson-plan-browser. |
| **Auth header** | Multi-user routes can use `X-Current-User-Id` ([backend/authorization.py](../../../backend/authorization.py)). Any generated client should attach this in **one** place (mutator/interceptor), not per call site. |

**Problem this addresses:** compile-time type drift between UI and server, scattered `fetch` strings, and harder code review—not “replace FastAPI” or change LLM vendor APIs.

---

## Recommendation: Orval

**Primary choice:** [Orval](https://orval.dev/) configured to generate a **TanStack React Query** client from the OpenAPI spec.

| Reason | Detail |
| ------ | ------ |
| **Matches existing stack** | The app already depends on `@tanstack/react-query`; Orval emits typed hooks, query keys, and underlying functions aligned with that pattern. |
| **Reviewability** | Named hooks and shared keys reduce ad hoc `fetch` and string URLs in components. |
| **Incremental adoption** | You can generate clients for **one router or tag** first and migrate call sites gradually; full replacement of [lesson-api](../../../shared/lesson-api/src/index.ts) is not required on day one. |

Configuration details (exact `orval.config.ts`, output paths, and package scripts) belong in implementation work; use the official Orval documentation for syntax and options.

---

## Feeding the generator

| Input | Notes |
| ----- | ----- |
| **Live spec** | With the backend running locally, OpenAPI JSON is typically at `http://127.0.0.1:8000/openapi.json` (FastAPI default path; confirm in your environment if customized). |
| **Pinned spec (optional)** | Export `openapi.json` into the repo and point Orval at the file so CI and offline builds are reproducible and diffs show API changes explicitly. |

**Headers:** Centralize `X-Current-User-Id` (and any future auth) in Orval’s mutator or equivalent so all generated calls stay consistent.

---

## Alternatives and deferrals

| Option | When to use |
| ------ | ----------- |
| **openapi-typescript** + **openapi-fetch** | Prefer if you want **types + a thin fetch wrapper** but **no** generated React Query hooks (you wire `useQuery` yourself). |
| **@hey-api/openapi-ts** | Prefer if you want a **generated SDK / modules** style with plugins; still a strong OpenAPI 3.x story. |
| **openapi-zod-client** | Defer unless you need **runtime** response validation (Zod) because you distrust the wire or hit real shape drift bugs. Adds weight versus types-only generation. |
| **Fern, Speakeasy, similar** | Better suited to **published multi-language SDKs** and productized APIs; **out of scope** for tightening contracts inside this monorepo unless requirements change. |

**Deprecated / legacy:** Older blog posts may reference `openapi-typescript-codegen`; maintainers have pointed adopters toward newer generators (e.g. Hey API). Prefer current tooling for new work.

---

## Non-goals

- Does **not** replace FastAPI, Pydantic, or the OpenAPI SSOT on the server.
- Does **not** describe **LLM provider** APIs (OpenAI, Anthropic, etc.); those are separate HTTPS clients inside the Python backend.
- Does **not** by itself fix **authorization** or **CORS** policy; those remain backend and deployment concerns.

---

## Related documentation

- [ADR-001: Technology stack](../../decisions/ADR-001-tech-stack.md) — local FastAPI, React/Tauri, localhost HTTP.
- [README.md](../../../README.md) — developer quick start (`uvicorn`, `npm run tauri dev`).
- Roadmap index: [../README.md](../README.md).

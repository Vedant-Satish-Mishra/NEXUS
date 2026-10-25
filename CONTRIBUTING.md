# Contributing to NEXUS

NEXUS is a four-person final-year B.E. IT project. Parallel development is organized strictly by tracks to avoid merge conflicts and preserve engineering contracts.

## 1. Team Tracks & Directory Scope

| Track | Scope | Directories Owned |
|---|---|---|
| **Track A** | Frontend & Animations | `frontend/`, `nexus frontend/` |
| **Track B** | Agents & LangGraph | `backend/app/agents/`, `backend/app/tools/` |
| **Track C** | RAG & Ingestion | `backend/app/rag/`, `data/knowledge/` |
| **Track D** | Backend, Auth & Deployment | `backend/app/api/`, `backend/app/db/`, `sandbox/`, `docker/` |

## 2. Branching Conventions

- **Main branch (`main`):** Protected branch. Only stable, fully tested releases are merged here.
- **Development branch (`develop`):** Daily integration branch.
- **Feature branches:** Must follow the naming format:
  ```text
  feat/<track>-<step>-<short-description>
  ```
  *Examples:*
  - `feat/A-1.A.1-motion-tokens`
  - `feat/B-2.B.3-planner-agent`
  - `feat/C-2.C.1-kb-ingestion`
  - `feat/D-1.D.2-jwt-auth`

## 3. Contracts-First Protocol

API schemas (`backend/app/schemas/`), event definitions, and OpenAPI contracts (`contracts/openapi.json`) are the single source of truth.

- **Rule:** Any change to API endpoints, request/response models, or SSE event types requires a PR labelled **`contract`** and must be approved by members from all four tracks before code relying on it is merged.

## 4. Definition of Done (DoD)

Before any PR can be merged:
1. Code compiles without errors (Python type hints, TypeScript build passes).
2. Automated tests are written and passing.
3. Acceptance Check from `nexus_implementation_guide.pdf` is explicitly demonstrated.
4. Corresponding step in `process.md` is updated.
5. No credentials, tokens, or plaintext secrets committed.

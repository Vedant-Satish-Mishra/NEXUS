# NEXUS implementation roadmap

## Evidence and status

The frontend implementation is developed in `nexus frontend/` as a high-fidelity React + TypeScript workspace based on the design mockups (`ChatGPT Image Oct 21...`) and requirements in `NEXUS_FRONTEND_DESIGN.md` and `PAGE_SPECIFICATIONS.md`. The backend and full pipeline milestones are detailed below.

## Phase 0 — decisions and contracts (P0)

- Confirm product domain, guest mode, browser targets, faculty rubric, MVP cut line, and canonical problem statement.
- Inspect the repository and record its actual frontend, backend, package manager, and deployment baseline.
- Agree API/event schemas, data ownership rules, agent configuration schema, and error model.
- Benchmark the target laptop and selected local model before feature work.

**Dependencies:** none. **Verification:** signed-off decisions, repository audit, sample API contract. **Acceptance:** every item marked confirmed, proposed, or deferred. **Review checkpoint:** team approves scope before coding.

## Phase 1 — foundation (P0)

- Establish application shell, authentication boundary, database migrations, health checks, streaming transport, and run checkpoint model.
- Implement deterministic Controller scaffolding, model-provider interface, embedding/vector-store interface, and audit logging contracts.
- Create design tokens and the responsive app shell; remove mock authentication/data only when a real replacement exists.

**Dependencies:** Phase 0. **Verification:** authenticated health path, migration up/down in disposable database, keyboard navigation through shell. **Acceptance:** resources have ownership checks and no secrets are committed. **Review checkpoint:** security/design review.

## Phase 2 — cognitive MVP (P0)

- Implement chat, Understanding JSON validation, tier routing, planner, editable approval interrupt, retrieval interface, reasoning streaming, and agent-selection UI.
- Persist run state so plan approval survives refresh/restart.

**Dependencies:** Phase 1. **Verification:** simple, document-grounded, and plan-required fixtures; paused-run resume test. **Acceptance:** no plan execution before approval; disabled agents cannot be invoked by the client. **Review checkpoint:** end-to-end demo.

## Phase 3 — knowledge and memory (P1)

- Add validated upload/ingestion, parsers, chunks with page metadata, hybrid retrieval, citations, memory proposals, confirmation, edit/delete, and scoped Knowledge/Memory pages.

**Dependencies:** Phase 2. **Verification:** ownership-isolation tests, delete-derived-data test, citation link test. **Acceptance:** insufficient evidence is surfaced rather than guessed. **Review checkpoint:** retrieval quality review.

## Phase 4 — reliability and tools (P1)

- Add calculator, file reader, local search, isolated Python service, tool approval UX, evaluation rules, bounded retry, feedback, Workflows, and Tools pages.

**Dependencies:** Phase 3. **Verification:** sandbox abuse tests, retry cap test, audit records, cancel/resume states. **Acceptance:** code never executes on the host and every tool call is approved/audited as required. **Review checkpoint:** security review.

## Phase 5 — learning, quality, release (P2)

- Add aggregated feedback strategy hints, dashboard/settings, golden-set evaluation, accessibility/responsive pass, packaging, backup/restore, and documentation updates.

**Dependencies:** Phase 4. **Verification:** 40-question golden set (proposed), visual/responsive/a11y checks, release checklist. **Acceptance:** results distinguish measured values from targets. **Review checkpoint:** faculty/release readiness review.

## Risks

VRAM pressure, malformed JSON, prompt injection, sandbox escape, cross-user leakage, and scope creep are high risks. Mitigate with context caps/benchmarking, schema validation plus fallback, untrusted-evidence handling, container isolation, authorization matrices, and phase gates respectively.

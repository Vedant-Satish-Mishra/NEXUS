# NEXUS testing and QA

No test runner or scripts were present, so no command is verified and no test has been run.

## Required test layers

- **Unit:** Controller tiers, schemas, ownership-filter builders, ranking, token budgets, state transitions.
- **Integration:** auth, streaming, checkpoints, document lifecycle, retrieval citation metadata, tool approval/audit.
- **End-to-end:** register/login, configure chat, plan approval, upload/query/delete file, memory confirmation/deletion, deny/run tool, resume paused run.
- **Security:** cross-user resources, malformed input, upload limits, injection, sandbox abuse.
- **UI:** keyboard, screen reader smoke tests, responsive widths, reduced motion, visual regression where practical.

## Quality gates

Proposed 40-question golden set measures retrieval hit@k/MRR, citation correctness, unanswerable refusal, coverage, latency, LLM calls, retries, and peak VRAM. Record measured results separately from targets. Before release: migrations tested, no console/server errors, critical journeys pass, dependencies reviewed, and design QA completed.

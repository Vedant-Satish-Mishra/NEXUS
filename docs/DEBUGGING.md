# NEXUS debugging guide

## Safe workflow

1. Reproduce with a minimal non-sensitive fixture and record expected/actual behaviour.
2. Identify the layer: UI, network/API, Controller/agent state, retrieval, model, database, sandbox, or deployment.
3. Inspect browser console/network and server logs without copying secrets, tokens, or user documents into tickets.
4. Check request IDs/run IDs, validation errors, authorisation scope, state transition history, and service health.
5. Make a minimal fix, add/regress a targeted test, and rerun the relevant journey.

## Product-specific checks

- Model unavailable: validate local Ollama health and selected model, then retry—do not silently use an external API.
- Missing sources: inspect document status, owner/conversation scope, chunks, and retriever results.
- Stuck approval: inspect persisted run state and checkpoint/stream replay, keeping interrupt node side-effect-free.
- UI layout: check at defined viewport sizes, zoom, long text, loading/error states, and reduced motion.

Real command names must be filled in only after `package.json`/service manifests exist.

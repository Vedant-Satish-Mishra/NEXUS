# NEXUS Agent Graph (Cognitive Pipeline)

Generated per Step 2.B.5 of the NEXUS Implementation Guide.

## Architecture Diagram

```mermaid
flowchart TD
  START([START]) --> understanding[understanding (LLM / fast fallback)]
  understanding --> controller[controller (Pure Code Router)]

  controller -->|tier: simple| reason[reason (Reasoning Agent)]
  controller -->|tier: document / complex| context_gather[context_gather]

  context_gather -->|tier: complex & planner enabled| plan_generate[plan_generate (Planner Agent)]
  context_gather -->|retrieval enabled| retrieval[retrieval (Retrieval Agent)]
  context_gather -->|otherwise| reason

  plan_generate --> plan_wait[plan_wait (Human-in-the-Loop Interrupt)]
  plan_wait -->|action: replan| plan_generate
  plan_wait -->|retrieval enabled| retrieval
  plan_wait -->|otherwise| reason

  retrieval --> reason
  reason --> finalize[finalize]
  finalize --> END([END])
```

## Tiers and Agent Execution
- **Tier 1 (Simple):** `START -> understanding -> controller -> reason -> finalize -> END`
- **Tier 2 (Document):** `START -> understanding -> controller -> context_gather -> retrieval -> reason -> finalize -> END`
- **Tier 3 (Complex):** `START -> understanding -> controller -> context_gather -> plan_generate -> plan_wait (interrupt) -> retrieval -> reason -> finalize -> END`

# NEXUS Server-Sent Events (SSE) Protocol (`contracts/events.md`)

All streaming output from `GET /api/v1/runs/{id}/events` follows this discriminated union on `"type"`.

---

## 1. Event Types Overview

| Event Type | Emitted When | Primary Payload |
|---|---|---|
| `queued` | GPU worker is busy processing another request | `position: int` |
| `run_started` | Pipeline execution starts | `run_id`, `tier`, `enabled_agents` |
| `node_started` | An individual agent/node starts | `node: str` |
| `node_finished` | An individual agent/node finishes | `node`, `summary`, `ms`, `status` |
| `understanding` | Structured JSON extracted | `understanding: {...}` |
| `plan_proposed` | Planner proposes steps for user approval | `run_id`, `plan: {...}`, `requires_approval: true` |
| `sources` | Retrieval finishes gathering document chunks | `sources: [{file, page, score, chunk_id}]` |
| `tool_proposed` | Approval-gated tool requested (e.g. Python) | `tool_id`, `tool`, `input`, `requires_approval` |
| `tool_result` | Tool execution completes | `tool_id`, `output`, `ms`, `status` |
| `token` | Reasoning model generates stream chunk | `content: str` |
| `evaluation` | Evaluation agent scores response | `score`, `checks`, `retry` |
| `memory_proposal` | System proposes user preferences to store | `proposals: [{id, kind, content, importance}]` |
| `final` | Response fully verified and complete | `message_id`, `content`, `citations` |
| `agent_hint` | A disabled agent would have improved the result | `agent`, `reason` |
| `heartbeat` | Every 15 seconds to keep proxies alive | `timestamp: int` |
| `error` | Failure occurred during execution | `code`, `message` |

---

## 2. Event Payloads & Examples

### `understanding`
```json
{
  "type": "understanding",
  "understanding": {
    "intent": "placement_preparation",
    "domain": "Java",
    "user_context": {
      "year": "4th Year",
      "branch": "IT",
      "time_available": "4 Months"
    },
    "requirements": ["Core Java", "DSA", "DBMS", "Interview Preparation"],
    "output_type": "4-month preparation plan",
    "complexity": "complex",
    "needs_retrieval": true,
    "needs_plan": true,
    "tools_required": [],
    "constraints": ["local execution"],
    "privacy_mode": "local_only"
  }
}
```

### `plan_proposed`
```json
{
  "type": "plan_proposed",
  "run_id": "run_7f3a9c",
  "requires_approval": true,
  "plan": {
    "goal": "4-Month Java Placement Preparation Plan",
    "steps": [
      {
        "id": "step_1",
        "title": "Core Java refresh",
        "detail": "OOP, collections, streams - weeks 1-3",
        "depends_on": [],
        "needs_retrieval": true
      },
      {
        "id": "step_2",
        "title": "DSA practice track",
        "detail": "arrays -> trees -> DP - weeks 2-12",
        "depends_on": ["step_1"],
        "needs_retrieval": true
      }
    ]
  }
}
```

### `sources`
```json
{
  "type": "sources",
  "sources": [
    {
      "file": "java_core.md",
      "page": 2,
      "score": 0.88,
      "chunk_id": "chk_9a1e4c",
      "snippet": "Java Virtual Machine memory model, garbage collection and collections framework."
    }
  ]
}
```

### `tool_proposed`
```json
{
  "type": "tool_proposed",
  "tool_id": "tool_exec_01",
  "tool": "python",
  "input": "import pandas as pd\ndf = pd.read_csv('placement_data.csv')\nprint(df.head())",
  "requires_approval": true
}
```

### `token`
```json
{
  "type": "token",
  "content": "Based on "
}
```

### `final`
```json
{
  "type": "final",
  "message_id": "msg_fin_01",
  "content": "Here is your customized 4-month preparation schedule...",
  "citations": [
    {
      "file": "java_core.md",
      "page": 2,
      "score": 0.88,
      "chunk_id": "chk_9a1e4c"
    }
  ]
}
```

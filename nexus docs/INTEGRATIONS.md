# NEXUS integrations

## Proposed required local services

| Service | Purpose | Authentication/configuration | Failure behaviour |
|---|---|---|---|
| Ollama + Qwen3 | local inference | host-local endpoint; exact variable unverified | show local-model unavailable and retry |
| PostgreSQL | accounts, runs, checkpoints, metadata | connection string/credentials; names unverified | fail safely; do not process state without persistence where required |
| ChromaDB | vector retrieval/semantic memory | local service/path; exact configuration unverified | report retrieval unavailable; do not fabricate citations |
| Python sandbox | approved isolated code execution | internal shared secret proposed | deny execution if unavailable |

Docker Compose, LangGraph, BGE Small, Neo4j, and Grafana are mentioned in the knowledge pack; exact versions/configuration are unverified. Web search is optional and off by default. Document each real environment variable only after source/config inspection; never place values in this file.

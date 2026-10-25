# NEXUS data model

## Status

PostgreSQL is proposed in the knowledge pack; no actual schema, migration tool, or database instance was available. The following is a proposed schema, not an implemented contract.

## Core entities

| Entity | Important fields | Rules |
|---|---|---|
| User | id, email, password_hash, created_at | email unique; never store plaintext password |
| Session/refresh token | id, user_id, token_hash, expires_at, revoked_at | store hash, revoke on logout/rotation |
| Conversation | id, user_id, title, agent_config | owner-scoped |
| Run | id, conversation_id, status, config_snapshot, timestamps | checkpointable lifecycle |
| PlanStep | id, run_id, position, text, status | unique run/position |
| Document | id, user_id, scope, filename, type, status | deletion cascades derived chunks/vectors |
| Memory | id, user_id, kind, content, importance, confirmed_at | only confirmed memories are recallable |
| Feedback/Learning signal | id, user_id, run_id, strategy_key, value | store aggregate signal, not unnecessary content |
| Audit event | id, user_id, run_id, action, result, created_at | immutable/security-relevant trail |

Index owner foreign keys, conversation/run timestamps, document status, memory user/recency, and retrieval metadata as justified by queries. Use migrations for every schema change; test upgrade and rollback/forward recovery. Define retention/deletion behaviour before implementation.

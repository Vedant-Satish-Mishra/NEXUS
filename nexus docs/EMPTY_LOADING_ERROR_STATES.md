# NEXUS empty, loading, and error states

## Confirmed product-specific states

- **New chat:** explain that configuration is required before the first run; offer preset selection.
- **No documents:** “No documents yet. Upload a file to use it as a source.”
- **No memories:** explain that only confirmed memories are saved.
- **Awaiting plan approval:** show plan, edit/replan/approve actions, and persistent run status.
- **Awaiting tool approval:** show requested code/input, Run, Edit and run, Deny.
- **Insufficient evidence:** say so, show available sources, and suggest upload/search refinement.
- **Ollama unavailable:** explain the local dependency and Retry; do not claim a cloud fallback.

Use skeletons only while layout/data shape is known, `aria-live` for meaningful async status, and a retry/recovery action where one exists. Do not celebrate failed/partial work as success.

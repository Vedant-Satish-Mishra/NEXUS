# NEXUS 10-Minute Demonstration Script (Step 5.D.3)

This script guides the viva or presentation demonstration of NEXUS on an RTX 4060 laptop, showcasing each cognitive agent, user approval checkpoints, and verifiable local-first operation.

---

## Preparation (2 minutes before presentation)

```powershell
# 1. Start Ollama and verify model
ollama serve
# 2. Run diagnostics check
powershell scripts/doctor.ps1
# 3. Launch backend & frontend
start.bat
```
Open browser to `http://localhost:5173`.

---

## 10-Minute Walkthrough

### Minute 0:00 - 1:30 | Introduction & Architectural Vision
- **Objective:** Introduce NEXUS as a local-first multi-agent cognitive architecture designed for resource-constrained hardware (8 GB VRAM).
- **Action:** Open the **Dashboard** page (`http://localhost:5173/dashboard`).
- **Talking Points:**
  - Emphasize the telemetry cards: Ollama host status, Postgres 16 DB, ChromaDB HNSW, and the isolated Python sandbox.
  - Highlight the 14-day activity chart and tier latency metrics: Tier 1 (~400 ms) vs Tier 3 (~2400 ms).
  - Emphasize zero data exfiltration: all computation runs locally on the host.

### Minute 1:30 - 3:00 | Tier 1: Instant Factual Q&A
- **Objective:** Demonstrate fast-path heuristic tier routing.
- **Action:**
  - Click **New Chat** with the **Fast** preset selected.
  - Ask: *"What is a HashMap in Java and what is its average lookup complexity?"*
- **Talking Points:**
  - Observe the live streaming response (~400 ms first token).
  - Point out that the Executive Controller classified this as **Tier 1**; no heavy Planner or RAG pipeline was invoked.

### Minute 3:00 - 5:00 | Tier 2: Hybrid RAG & Grounded Citations
- **Objective:** Demonstrate FastEmbed + BM25 Reciprocal Rank Fusion and inline citations.
- **Action:**
  - Switch to **Balanced** preset.
  - Ask: *"Explain database transactions and ACID properties according to our database notes."*
- **Talking Points:**
  - Notice the **Understanding Card** displaying intent, technical domain (`DBMS`), and Tier 2 classification.
  - Point out the superscript citation chips `[S1]`, `[S2]`.
  - Click a citation chip to open the source drawer showing exact file, page, and chunk text.

### Minute 5:00 - 7:30 | Tier 3: Multi-Agent Planning & Human-in-the-Loop Approval
- **Objective:** Demonstrate plan generation, topological sort, user edit checkpoint, and tool execution.
- **Action:**
  - Switch to **Full** preset.
  - Prompt: *"Write a Python script to calculate the Fibonacci series up to 20 numbers, verify the calculation, and summarize the recurrence relation."*
- **Talking Points:**
  - The **Plan Approval Card** appears with 4 dependency-ordered steps.
  - Show inline editing: drag to reorder or edit step title.
  - Click **Approve Plan**.
  - The system initiates the execution loop: the **Python Approval Dialog** opens with code review, sandbox limits (10s, 512 MB, no network), and action buttons.
  - Click **Run**: code executes inside the container, stdout returns to reasoning, and the **Evaluation Agent** verifies syntax and numeric accuracy.

### Minute 7:30 - 8:45 | Memory Agent & User Consent Invariant
- **Objective:** Prove that memory is never silently captured.
- **Action:**
  - Below the completed assistant message, observe the **Memory Proposal Chip**:
    `"Remember: User is working on Fibonacci series algorithms and recurrence relations."`
  - Show the **Save**, **Edit**, and **Dismiss** buttons.
  - Click **Save**.
  - Navigate to the **Memory** page (`http://localhost:5173/memory`): the confirmed memory is now listed under Long-term memories.

### Minute 8:45 - 10:00 | Adaptive Learning, Settings & Data Sovereignty
- **Objective:** Demonstrate feedback signals and full data control.
- **Action:**
  - Return to Chat and click the **Thumbs Up** button under the assistant response.
  - Navigate to **Settings** (`http://localhost:5173/settings`):
    - Highlight the **VRAM guidance** on model profiles (Fast 4B vs Quality 8B).
    - Click **Download ZIP** to demonstrate GDPR-compliant portable data export.
    - Show the **Reset Learning Data** and **Permanently Delete Account** modal protections.
- **Closing Statement:** NEXUS delivers state-of-the-art cognitive agency, transparent human oversight, and absolute privacy on commodity consumer hardware.

# NEXUS Frontend

A high-fidelity, local-first React + TypeScript single-page application for the **NEXUS AI Cognitive System**, designed according to the specifications in `nexus docs/` and matching the UI design mockups.

## Key Features

1. **Persistent Three-Region Workspace**:
   - **Left Sidebar**: Preset controls (Fast, Balanced, Full), individual agent toggles (Controller, Planner, Retrieval, Reasoning, Memory, Learning, Evaluation), conversation list, and navigation to Knowledge, Memory, Workflows, Tools, and Settings.
   - **Center Workspace**: Chat conversation, Understood card (intent, domain, requirements, complexity tier), interactive Plan Approval card (drag/reorder, inline editing, step addition/deletion, re-plan with feedback), Python sandbox approval, citations, memory proposal chips, and responsive composer with voice and file attachment.
   - **Right Agent Graph Panel**: Live interactive pipeline flowchart (Understanding → Controller → Memory/Learning → Planner → Retrieval/Execute → Reasoning → Evaluation → Final Answer with re-plan loop), paused run checkpoint indicator, and cited sources inspector.
2. **Knowledge Base Page**:
   - Document inventory (PDF, DOCX, MD, TXT) with local index status (Indexed / Processing).
   - Document detail inspection drawer with preview, page-level citation highlighter, and citation copy.
   - File upload modal with format filtering and ChromaDB indexing simulation.
3. **Consent-First Memory Page**:
   - "Only confirmed memories are saved" policy.
   - Pending memory proposals with Save / Edit / Dismiss controls.
   - Categorised confirmed memories (Goal, Preference, Context, Constraint) with importance ratings (High, Medium, Low).
   - Complete memory purge capability with confirmation dialog.
4. **Workflows & Runs Page**:
   - Run history with status filters (Running, Awaiting plan approval, Completed, Failed).
   - Interactive execution stepper timeline showing node completion times and details.
   - Run resume into active chat and cancel operations.
5. **Tools & Python Sandbox**:
   - Tool permission contracts for AST Calculator, File Reader, Local Knowledge Search, and Python Sandbox.
   - Interactive code editor with sandbox runner terminal and simulated isolated container output.
6. **Settings & Telemetry**:
   - Dark, Light, and System theme switching.
   - Reduced motion accessibility toggle.
   - Font scaling (Small, Medium, Large).
   - Model profile selection (Fast: Qwen3 4B vs Quality: Qwen3 8B Q4).
   - Learning strategy adaptation toggle and reset control.
7. **Authentication**:
   - Local-first Login and Registration views matching brand lockup and security requirements.

## Quick Start

```bash
# Navigate to the frontend directory
cd "nexus frontend"

# Install dependencies (already installed)
npm install

# Start development server
npm run dev

# Build production bundle
npm run build

# Preview build
npm run preview
```

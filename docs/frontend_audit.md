# NEXUS Frontend Audit & Design Baseline (`docs/frontend_audit.md`)

**Track:** Track A (Frontend & Animations)  
**Date:** 2026-10-21  
**Guide Reference:** Step 0.5  

---

## 1. Storage, Auth & API Inventory (Legacy vs Target Replacement)

| Legacy Usage | Location in Legacy / Prototype | Target Replacement in NEXUS v1 |
|---|---|---|
| Direct `fetch` to Ollama (`localhost:11434`) | Client-side chat services | **Replaced.** All LLM calls pass through FastAPI (`POST /api/v1/runs` + SSE streaming). Browser never talks to Ollama directly. |
| Plaintext passwords & mock user table | `localStorage.getItem("users")` | **Replaced.** Backend bcrypt hashing (8..72 bytes), JWT access token in memory, HttpOnly refresh cookie. |
| Chat history in `localStorage` | `localStorage.getItem("chats")` | **Replaced.** PostgreSQL `conversations` and `messages` tables accessed via `/api/v1/conversations`. |
| 3-message guest limit | Client-side counter | **Replaced.** Authenticated session required for persistent chats; clean 401 redirect to `/login`. |
| Subscriptions, billing & admin console | Legacy mock pages | **Removed.** Explicitly out of scope per PRD and owner decisions. |
| Theme & visual preferences | `localStorage.getItem("nexus_theme")` | **Retained.** UI visual settings (theme, reduced motion, font size) persist in localStorage. |

---

## 2. Component Tree

```text
App (Root Provider & Theme Shell)
├── Sidebar (Navigation & Controls)
│   ├── BrandLockup (Logo + Title)
│   ├── NewChatButton
│   ├── PresetSelector (Fast / Balanced / Full)
│   ├── AgentToggleRows (Controller, Planner, Retrieval, Reasoning, Memory, Learning, Evaluation)
│   ├── ConversationList (Recent chats + delete)
│   ├── NavigationLinks (Knowledge, Memory, Workflows, Tools, Dashboard, Settings)
│   └── OllamaStatusIndicator
├── CenterWorkspace (Dynamic Page Route)
│   ├── ChatWorkspace
│   │   ├── ChatHeader (Title + Rating)
│   │   ├── MessageList
│   │   │   ├── UserMessageBubble
│   │   │   └── AssistantMessage
│   │   │       ├── UnderstandingCard (Chips + Tier)
│   │   │       ├── PlanApprovalCard (Steps + Reorder + Edit + Actions)
│   │   │       ├── ToolApprovalCard (Sandbox code review + Run/Deny)
│   │   │       ├── CitationChips
│   │   │       └── MemoryProposalCard (Save/Edit/Dismiss)
│   │   └── ChatComposer (Textarea, Attach, Mic, Send)
│   ├── KnowledgePage (Document table, upload modal, preview drawer)
│   ├── MemoryPage (Proposals tray, confirmed memory cards, wipe modal)
│   ├── WorkflowsPage (Runs list, stepper timeline, resume action)
│   ├── ToolsPage (Tool contracts, live sandbox code runner, calculator)
│   ├── DashboardPage (Telemetry, tier routing distribution, model status)
│   └── SettingsPage (Theme, reduced motion, font size, model profile, learning reset)
├── AgentGraphPanel (Right Context Column)
│   ├── LiveFlowchart (10 Nodes + Re-plan loop)
│   ├── CheckpointStateCard (Paused run indicator)
│   └── SourcesDrawer (Document chunk viewer)
└── NewChatModal (Initial conversation setup)
```

---

## 3. CSS Variables & Theme Definitions

```css
/* Dark Theme (Default) */
:root, [data-theme="dark"] {
  --nx-bg: #18110c;
  --nx-bg-subtle: #241710;
  --nx-surface-dark: #2b1c13;
  --nx-border-dark: #3d291d;
  --nx-panel: #fdfbf7;
  --nx-panel-subtle: #f7f2ea;
  --nx-border: #e6decb;
  --nx-border-card: #d8cbb8;
  --nx-text: #1e140f;
  --nx-text-inverse: #fbf8f2;
  --nx-text-muted: #786558;
  --nx-primary: #f25c24;
  --nx-primary-hover: #d94c17;
  --nx-gold: #d97706;
}

/* Light Theme */
[data-theme="light"] {
  --nx-bg: #f5ede4;
  --nx-bg-subtle: #eae1d7;
  --nx-surface-dark: #e0d5c8;
  --nx-border-dark: #c2b3a1;
  --nx-panel: #ffffff;
  --nx-panel-subtle: #f9f6f0;
  --nx-border: #ded5c5;
  --nx-border-card: #cfc3b0;
  --nx-text: #1a110a;
  --nx-text-inverse: #1e140f;
  --nx-text-muted: #6e5849;
  --nx-primary: #e65100;
  --nx-primary-hover: #bf4300;
  --nx-gold: #b45309;
}
```

---

## 4. Motion Tokens & Accessibility Rules

```typescript
export const dur = {
  fast: 0.15,
  base: 0.25,
  slow: 0.40
} as const;

export const ease = {
  out: [0.22, 1, 0.36, 1],
  inOut: [0.65, 0, 0.35, 1]
} as const;

export const spring = {
  soft: { type: 'spring', stiffness: 260, damping: 28 },
  snappy: { type: 'spring', stiffness: 350, damping: 22 }
} as const;
```

**Reduced Motion Invariant:**
When `reducedMotion` is toggled on or system `prefers-reduced-motion` is detected:
- Transition durations drop to `0s`.
- Node pulse glow and graph flow animations are disabled.
- Status is conveyed through static color badges and text labels.

---

## 5. TypeScript Service Interfaces

```typescript
export interface AuthService {
  login(email: string, password?: string): Promise<{ token: string; user: any }>;
  register(name: string, email: string, password?: string): Promise<any>;
  refresh(): Promise<string>;
  logout(): Promise<void>;
  me(): Promise<any>;
}

export interface ConversationService {
  list(): Promise<any[]>;
  get(id: string): Promise<any>;
  create(preset: string, config: any): Promise<any>;
  updateAgents(id: string, config: any): Promise<any>;
  delete(id: string): Promise<void>;
}

export interface RunService {
  start(conversationId: string, message: string, fileIds?: string[]): Promise<{ runId: string }>;
  subscribe(runId: string, onEvent: (evt: any) => void): () => void;
  decidePlan(runId: string, decision: { action: string; steps?: any[]; feedback?: string }): Promise<void>;
  decideTool(runId: string, toolId: string, decision: { action: string; code?: string }): Promise<void>;
  cancel(runId: string): Promise<void>;
}

export interface FileService {
  list(): Promise<any[]>;
  upload(file: File, scope: string): Promise<any>;
  delete(fileId: string): Promise<void>;
}

export interface MemoryService {
  list(kind?: string): Promise<any[]>;
  decide(proposalId: string, decision: { action: string; content?: string }): Promise<void>;
  delete(memoryId: string): Promise<void>;
  wipeAll(): Promise<void>;
}

export interface SettingsService {
  get(): Promise<any>;
  update(settings: any): Promise<any>;
  resetLearning(): Promise<void>;
}
```

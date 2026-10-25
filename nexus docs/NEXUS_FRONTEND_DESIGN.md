# NEXUS Frontend Design Specification

## 1. Direction

Build NEXUS as a local AI workspace, not a generic chatbot. The visual language should keep the character of the supplied work:

- Dark cocoa application background, cream content surfaces, burnt-orange primary action color, and muted gold for selected or active states.
- The hand-drawn outline is a brand accent around the app frame, logo, and occasional cards. Do not put sketch borders around every small control; that would hurt clarity.
- Use the existing NEXUS logo on the splash screen, landing page, authentication shell, and desktop sidebar.
- Use clear modern sans-serif body text; reserve the expressive serif/display treatment for the NEXUS wordmark or large page titles only.
- Respect reduced-motion settings. Animate only opacity and transforms.

The supplied logo and start/front page are considered existing work. The rest of this document starts after the user chooses **Start NEXUS**.

## 2. Scope: 13 visible screens

NEXUS should have 13 user-visible screens in version 1. The product requirements already define 11 application routes; the existing splash and landing views make the practical frontend scope 13 screens.

1. **Splash / start** — existing logo reveal; one Continue control.
2. **Landing page** — existing or refine; project promise, local-first note, Start NEXUS and Sign in.
3. **Login** — email, password, show/hide password, Sign in, Register link.
4. **Register** — name, email, password, confirm password, show/hide password, Create account, Sign in link.
5. **New chat setup** (`/chat`) — choose Fast, Balanced, or Full preset; optional agent choices; model profile; plan approval preference; Start chat.
6. **Chat workspace** (`/chat/:id`) — primary screen; conversation, understanding result, plans, approvals, sources, and agent graph.
7. **Knowledge** (`/knowledge`) — upload, inspect, search, filter, retry, and delete indexed documents.
8. **Memory** (`/memory`) — view, search, edit, delete, and consent-manage saved memories.
9. **Workflows** (`/workflows`) — all running, paused, completed, failed, and cancelled runs.
10. **Workflow detail** (`/workflows/:runId`) — event timeline, plan/tool approval state, retry status, and resume/cancel actions.
11. **Tools** (`/tools`) — supported tools, permission expectations, and audit/history view.
12. **Dashboard** (`/dashboard`) — personal activity and quality signals; no fake business metrics.
13. **Settings** (`/settings`) — appearance, accessibility, privacy, model preference, learning toggle, account session controls.

A simple not-found page is also required, but it is an error state rather than a product screen.

## 3. Navigation and app shell

After login, use one persistent app shell.

### Desktop

- **Left sidebar (about 280 px):** logo, New chat button, agent preset controls, agent toggle controls when starting a new chat, recent chat list, local-model status, profile/settings entry.
- **Centre panel (flexible; minimum about 600 px):** current page. In chat, this holds messages, plan approval cards, tool approval cards, citations, and the composer.
- **Right context panel (about 320 px):** active chat only. It holds the live agent graph, run status, sources, evaluation/confidence details, and a compact run resume notice.

### Tablet and mobile

- At tablet width, collapse the right context panel into a drawer triggered by **Agents & sources**.
- On phones, use one conversation column. Sidebar navigation becomes a sheet/drawer. The agent graph, citations, plan controls, and tool approval details become bottom sheets or inline expandable cards.
- Do not make the three-column desktop layout merely shrink; it becomes unreadable.

## 4. The chat screen: required UI

This is the heart of NEXUS and should be designed first.

### Left sidebar controls

| Element | Count / rule | Notes |
|---|---:|---|
| New chat | 1 | Primary orange button. |
| Presets | 3 choices | Fast, Balanced, Full; use a segmented control, not three separate primary buttons. |
| Locked agent indicators | 2 | Controller and Reasoning are always enabled; display them as locked/on. |
| Optional agent toggles | 5 | Planner, Retrieval, Memory, Learning, Evaluation. Only change before the next run. |
| Recent chats | Dynamic | Each row opens a chat; show menu only on hover/focus. |
| Model status | 1 | e.g. “Ollama running · qwen3:4b”; status, not a button. |

### Centre conversation area

| Component | Main actions |
|---|---|
| Chat header | Rename conversation, overflow menu. |
| User message | Copy, edit/retry when supported. |
| Assistant answer | Copy, feedback up/down, citations, expand details. |
| Understanding card | Expand/collapse the structured intent, requirements, and routing tier. |
| Plan approval card | Edit/reorder steps, Add step, Delete step, Approve plan, Re-plan with feedback, Approve & do not ask again. |
| Tool approval card | View code/input, Edit, Run, Deny. Python must never run from a single implicit click. |
| Composer | Attach file, optional voice input if retained, send. |

### Right panel

| Component | Required content |
|---|---|
| Agent graph | Understanding, Controller, Memory, Learning, Planner, Retrieval, Execute, Reasoning, Evaluation, Final. Node states: idle, active, waiting, done, skipped, disabled, error. |
| Run status | Queued, running, awaiting plan approval, awaiting tool approval, completed, failed, cancelled, expired. |
| Sources | Citation chips with filename and page; clicking opens the document preview at the cited location. |
| Evaluation | Confidence / low-confidence notice, retry message, and brief user-safe explanation. |

## 5. Button inventory

Do not try to reach a fixed “total number of buttons”; document rows, chat history, citations, and plan steps are dynamic. Instead, build this stable action inventory.

| Area | Initial action controls | Notes |
|---|---:|---|
| Splash and landing | 3 | Continue, Start NEXUS, Sign in. |
| Authentication | 7–9 | Submit, password visibility, and navigation links; add no social login in v1. |
| New chat setup | 11–14 | Preset selection, 5 optional agent switches, model profile, auto-approve, Start chat. |
| Chat baseline | 8 | New chat, attach, optional voice, send, copy, feedback up/down, Agents & sources drawer. |
| Each plan card | 6 + step controls | Approve, re-plan, future auto-approve, add/edit/reorder/delete steps. |
| Each tool request | 3 | Run, Edit and run, Deny. |
| Knowledge | 7 | Upload, search, filter, preview, retry, delete, promote. |
| Memory | 7 | Search, filter, edit, delete, delete all, memory toggle, learning reset. |
| Workflows | 4 | Search/filter, open, resume, cancel where valid. |
| Settings | 6–10 | Theme, reduced motion, font size, model, privacy, learning, logout; scope depends on final settings decisions. |

Use one obvious primary action per section. Examples: **Start chat**, **Send**, **Approve plan**, **Run**, **Upload files**, **Save changes**. All other actions should be secondary, ghost, icons with accessible labels, or an overflow menu.

## 6. Reusable components to design before pages

Create these as reusable components, not one-off page markup:

1. `AppShell`
2. `BrandLockup`
3. `SidebarNavItem`
4. `PresetSelector`
5. `AgentToggleRow`
6. `LocalModelStatus`
7. `ChatMessage`
8. `UnderstandingCard`
9. `PlanStepCard`
10. `PlanApprovalCard`
11. `ToolApprovalCard`
12. `CitationChip`
13. `AgentGraph`
14. `RunStatusBadge`
15. `DocumentRow`
16. `MemoryCard`
17. `EmptyState`, `LoadingState`, `ErrorState`, and `ConfirmDialog`

## 7. Page-level requirements

### Knowledge

- Drag-and-drop upload plus browse button.
- Processing state: uploaded, parsing, indexing, ready, failed.
- Filters: scope (chat/personal/preloaded), file type, status.
- File detail drawer: metadata, pages/slides, chunk count, index state, Delete.
- Deletion must use a confirmation dialog because it removes derived chunks/vectors as well.

### Memory

- A visible explanation that memory is only saved after confirmation.
- Memory proposal chips inside chat: Save, Edit, Dismiss.
- Separate confirmed memory list with type, importance, date, source chat, edit, and delete.
- “Delete all memories” requires a typed or explicit confirmation.

### Workflows and workflow detail

- The list page uses status, date, and chat filters.
- The detail page uses an event timeline, not a generic log wall.
- Clear resume action for a paused plan/tool approval and cancel action only while valid.

### Tools

- Show Calculator, File reader, Local knowledge search, and Python sandbox.
- Explain the permission contract beside the tool, especially that Python needs explicit per-run approval.
- Do not show web search as active by default; it is optional/future.

### Dashboard

- Show personal/local facts: recent runs, document count, confirmed memory count, feedback history, and model health.
- Do not invent adoption, revenue, accuracy, or “AI performance” values before NEXUS has measurement data.

### Settings

- Appearance: theme, contrast, font size, reduced motion.
- Intelligence: Fast/Quality default model profile, learning toggle, reset learning data.
- Privacy: memory explanation/toggle, external web-search preference if later enabled.
- Account: session/logout and account deletion entry.

## 8. Essential states

Every main page needs designs for:

- first use / empty state;
- loading / streaming;
- success;
- recoverable error;
- no search results;
- offline or Ollama unavailable;
- permission required;
- destructive-action confirmation.

For chat, additionally design: awaiting plan approval, awaiting tool approval, low-confidence answer, retrying, paused run restored after refresh, and disabled-agent hint.

## 9. Recommended implementation order

### Phase A — foundation

1. Design tokens: colors, typography, spacing, radii, outline treatment, focus states.
2. App shell, sidebar, responsive navigation, logo lockup.
3. Login and register pages.

### Phase B — usable core

4. New chat setup.
5. Chat messages, composer, streaming state.
6. Understanding and plan approval cards.
7. Agent graph and sources drawer/panel.

### Phase C — knowledge and trust

8. Knowledge upload/library and document preview.
9. Memory proposals and Memory page.
10. Tool approval UI and Workflows.

### Phase D — finish

11. Tools, Dashboard, Settings.
12. Mobile/tablet adaptations, accessibility pass, animation and empty/error states.
13. Connect real API contracts, then remove all mock data.

## 10. Decisions to confirm before final visual design

- Whether the already-built “front page after start” is the landing page or the `/chat` new-chat setup view.
- Whether voice input from the older UI remains in v1; it is not part of the documented v1 scope.
- Whether guest mode exists; the knowledge pack marks this undecided.
- Whether default appearance is dark as shown in the mockup, light, or follows the operating system.
- Exact supported breakpoints/browsers, still undecided in the project requirements.

## 11. Acceptance checklist

- A new user can create an account, choose an agent preset, send a first message, understand why a plan is waiting, and approve or change it without reading documentation.
- A user can see exactly which agents ran, which sources were used, and what is saved as memory.
- Every destructive or executable action has a clear confirmation or approval path.
- Keyboard focus is visible; every icon-only control has an accessible label; contrast and reduced motion are supported.
- The app remains useful on mobile without squeezing the three-column desktop screen.

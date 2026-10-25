# NEXUS component guidelines

No existing frontend library was found. Define implementation components only after inspecting the actual stack.

## Reusable boundaries

`AppShell`, `BrandLockup`, `SidebarNavItem`, `PresetSelector`, `AgentToggleRow`, `ChatMessage`, `UnderstandingCard`, `PlanApprovalCard`, `PlanStep`, `ToolApprovalCard`, `CitationChip`, `AgentGraph`, `RunStatusBadge`, `DocumentRow`, `MemoryCard`, `Dialog`, and standard empty/loading/error states.

## Reuse rules

Use one Button, Input, Select, Toggle, Dialog, Badge, Card, Table, and Alert family with documented variants/states. Compose product cards from primitives; do not fork controls per page. Every component documents default, hover, focus-visible, disabled, loading, error, and responsive states as relevant.

Card usage is purposeful: a distinct plan, tool approval, memory, or document—not every paragraph. Destructive variants always require the design-system danger token and confirmation where irreversible.

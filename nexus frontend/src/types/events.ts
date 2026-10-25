/**
 * NEXUS Server-Sent Events (SSE) TypeScript Protocol
 * Discriminated union on property 'type'
 */

export interface UnderstandingPayload {
  intent: string;
  domain?: string;
  user_context: Record<string, string>;
  requirements: string[];
  output_type: string;
  complexity: 'simple' | 'document' | 'complex';
  needs_retrieval: boolean;
  needs_plan: boolean;
  tools_required: string[];
  constraints: string[];
  privacy_mode: 'local_only' | 'web_allowed';
}

export interface PlanStepPayload {
  id: string;
  title: string;
  detail: string;
  depends_on?: string[];
  needs_retrieval?: boolean;
  tool?: string;
}

export interface PlanPayload {
  goal: string;
  steps: PlanStepPayload[];
}

export interface CitationItemPayload {
  file: string;
  page: number;
  score: number;
  chunk_id: string;
  snippet?: string;
}

export interface MemoryProposalPayload {
  id: string;
  kind: 'long_term' | 'episodic';
  content: string;
  status: 'pending' | 'accepted' | 'edited' | 'rejected';
  importance: 'high' | 'medium' | 'low';
}

export type SSEEvent =
  | { type: 'queued'; position: number }
  | { type: 'run_started'; run_id: string; tier: 1 | 2 | 3; enabled_agents: string[] }
  | { type: 'node_started'; node: string }
  | { type: 'node_finished'; node: string; summary: string; ms: number; status: 'ok' | 'skipped' | 'error' }
  | { type: 'understanding'; understanding: UnderstandingPayload }
  | { type: 'plan_proposed'; run_id: string; plan: PlanPayload; requires_approval: boolean }
  | { type: 'sources'; sources: CitationItemPayload[] }
  | { type: 'tool_proposed'; tool_id: string; tool: string; input: string; requires_approval: boolean }
  | { type: 'tool_result'; tool_id: string; tool: string; output: string; ms: number; status: 'ok' | 'denied' | 'error' }
  | { type: 'token'; content: string }
  | { type: 'evaluation'; score: number; checks: Record<string, boolean>; retry: boolean; critique?: string }
  | { type: 'memory_proposal'; proposals: MemoryProposalPayload[] }
  | { type: 'final'; message_id: string; content: string; citations: CitationItemPayload[] }
  | { type: 'agent_hint'; agent: string; reason: string }
  | { type: 'error'; code: string; message: string }
  | { type: 'heartbeat'; timestamp: number };

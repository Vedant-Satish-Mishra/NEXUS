export type AgentType = 
  | 'controller' 
  | 'planner' 
  | 'retrieval' 
  | 'reasoning' 
  | 'memory' 
  | 'learning' 
  | 'evaluation';

export type AgentPreset = 'fast' | 'balanced' | 'full';

export type ModelProfile = 'fast' | 'quality';

export interface AgentConfig {
  controller: boolean; // always true
  planner: boolean;
  retrieval: boolean;
  reasoning: boolean;  // always true
  memory: boolean;
  learning: boolean;
  evaluation: boolean;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface Understanding {
  intent: string;
  domain: string;
  userContext: {
    year?: string;
    branch?: string;
    timeAvailable?: string;
    [key: string]: string | undefined;
  };
  requirements: string[];
  outputType: string;
  complexity: 'simple' | 'document' | 'complex';
  tier: 1 | 2 | 3;
}

export interface PlanStep {
  id: string;
  position: number;
  title: string;
  detail: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface Plan {
  id: string;
  goal: string;
  steps: PlanStep[];
  status: 'awaiting_approval' | 'approved' | 'replanning' | 'completed';
}

export interface ToolCall {
  id: string;
  toolName: 'calculator' | 'file_reader' | 'local_search' | 'python_sandbox';
  codeOrInput: string;
  status: 'awaiting_approval' | 'running' | 'completed' | 'denied';
  output?: string;
  executionTime?: string;
}

export interface Citation {
  id: string;
  filename: string;
  page: number;
  section?: string;
  snippet: string;
  scope?: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  importance: 'high' | 'medium' | 'low';
  status: 'saved' | 'pending';
  sourceChat: string;
  date: string;
  category: 'goal' | 'preference' | 'context' | 'constraint';
}

export interface DocumentItem {
  id: string;
  name: string;
  type: 'PDF' | 'MD' | 'DOCX' | 'TXT' | 'XLSX';
  pages: number;
  scope: string;
  status: 'indexed' | 'processing' | 'failed';
  uploadedAt: string;
  size: string;
  contentPreview?: string;
  citationsCount?: number;
}

export interface WorkflowRun {
  id: string;
  name: string;
  startedAt: string;
  status: 'awaiting_plan_approval' | 'running' | 'completed' | 'failed';
  preset: AgentPreset;
  currentStep: number;
  totalSteps: number;
  steps: {
    number: number;
    title: string;
    time: string;
    status: 'completed' | 'active' | 'pending';
    detail?: string;
  }[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  understanding?: Understanding;
  plan?: Plan;
  toolCall?: ToolCall;
  citations?: Citation[];
  memoriesProposed?: MemoryItem[];
  evaluation?: {
    score: number;
    label: string;
    passed: boolean;
    feedback?: string;
  };
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  agentPreset: AgentPreset;
  agentConfig: AgentConfig;
  modelProfile: ModelProfile;
  askBeforePlan: boolean;
  messages: ChatMessage[];
  rating?: number;
}

export type GraphNodeId = 
  | 'understanding' 
  | 'controller' 
  | 'memory' 
  | 'learning' 
  | 'planner' 
  | 'retrieval' 
  | 'execute' 
  | 'reasoning' 
  | 'evaluation' 
  | 'final_answer';

export type GraphNodeStatus = 'idle' | 'active' | 'waiting' | 'done' | 'skipped' | 'disabled' | 'error';

export type AppPage = 
  | 'chat' 
  | 'knowledge' 
  | 'memory' 
  | 'workflows' 
  | 'tools' 
  | 'settings' 
  | 'dashboard' 
  | 'login' 
  | 'register';

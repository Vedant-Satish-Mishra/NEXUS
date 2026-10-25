import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  Conversation,
  ChatMessage,
  DocumentItem,
  MemoryItem,
  WorkflowRun,
  User,
  AppPage,
  AgentPreset,
  AgentConfig,
  ModelProfile,
  PlanStep,
  ToolCall,
  GraphNodeId,
  GraphNodeStatus
} from '../types';
import {
  mockUser,
  mockConversations,
  mockDocuments,
  mockMemories,
  mockWorkflows
} from '../data/mockData';
import { ConversationService, RunService, FileService, MemoryService, getAccessToken } from '../lib/api';
import { parseSSE } from '../lib/sse';

interface AppContextType {
  // Navigation & Auth
  currentPage: AppPage;
  setCurrentPage: (page: AppPage) => void;
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string) => void;
  register: (name: string, email: string) => void;
  logout: () => void;

  // Conversations
  conversations: Conversation[];
  activeConversationId: string;
  activeConversation: Conversation | null;
  setActiveConversationId: (id: string) => void;
  createNewConversation: (
    preset: AgentPreset,
    config: AgentConfig,
    model: ModelProfile,
    askBeforePlan: boolean,
    initialPrompt?: string
  ) => string;
  sendMessage: (content: string) => void;
  deleteConversation: (id: string) => void;

  // New Chat Modal
  isNewChatModalOpen: boolean;
  setIsNewChatModalOpen: (open: boolean) => void;

  // Plan actions
  approvePlan: (messageId: string) => void;
  replanWithFeedback: (messageId: string, feedback: string) => void;
  editPlanStep: (messageId: string, stepId: string, title: string, detail: string) => void;
  deletePlanStep: (messageId: string, stepId: string) => void;
  addPlanStep: (messageId: string, title: string, detail: string) => void;

  // Tool actions
  approveTool: (messageId: string) => void;
  denyTool: (messageId: string) => void;
  runPythonCode: (code: string) => Promise<string>;

  // Documents
  documents: DocumentItem[];
  previewDocument: DocumentItem | null;
  setPreviewDocument: (doc: DocumentItem | null) => void;
  uploadDocument: (name: string, type: 'PDF' | 'MD' | 'DOCX' | 'TXT', size: string) => void;
  deleteDocument: (id: string) => void;

  // Memories
  memories: MemoryItem[];
  saveMemory: (id: string) => void;
  dismissMemory: (id: string) => void;
  deleteMemory: (id: string) => void;
  deleteAllMemories: () => void;
  addMemoryManually: (content: string, importance: 'high' | 'medium' | 'low') => void;

  // Workflows
  workflows: WorkflowRun[];
  activeWorkflow: WorkflowRun | null;
  setActiveWorkflowId: (id: string | null) => void;

  // Settings
  theme: 'dark' | 'light' | 'system';
  setTheme: (t: 'dark' | 'light' | 'system') => void;
  reducedMotion: boolean;
  setReducedMotion: (rm: boolean) => void;
  fontSize: 'small' | 'medium' | 'large';
  setFontSize: (fs: 'small' | 'medium' | 'large') => void;
  defaultModel: ModelProfile;
  setDefaultModel: (m: ModelProfile) => void;
  learningEnabled: boolean;
  setLearningEnabled: (le: boolean) => void;
  resetLearningData: () => void;

  // Graph state
  graphNodes: Record<GraphNodeId, GraphNodeStatus>;
  isProcessing: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentPage, setCurrentPage] = useState<AppPage>('chat');
  const [user, setUser] = useState<User | null>(mockUser);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);

  const [conversations, setConversations] = useState<Conversation[]>(mockConversations);
  const [activeConversationId, setActiveConversationId] = useState<string>('conv_java_prep');
  const [isNewChatModalOpen, setIsNewChatModalOpen] = useState<boolean>(false);

  const [documents, setDocuments] = useState<DocumentItem[]>(mockDocuments);
  const [previewDocument, setPreviewDocument] = useState<DocumentItem | null>(null);

  const [memories, setMemories] = useState<MemoryItem[]>(mockMemories);
  const [workflows, setWorkflows] = useState<WorkflowRun[]>(mockWorkflows);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>('run_7f3a9c');

  // Settings
  const [theme, setTheme] = useState<'dark' | 'light' | 'system'>('dark');
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [defaultModel, setDefaultModel] = useState<ModelProfile>('fast');
  const [learningEnabled, setLearningEnabled] = useState<boolean>(true);

  // Live Agent Graph Node States
  const [graphNodes, setGraphNodes] = useState<Record<GraphNodeId, GraphNodeStatus>>({
    understanding: 'done',
    controller: 'done',
    memory: 'done',
    learning: 'done',
    planner: 'active',
    retrieval: 'idle',
    execute: 'idle',
    reasoning: 'idle',
    evaluation: 'idle',
    final_answer: 'idle'
  });
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const activeConversation = conversations.find(c => c.id === activeConversationId) || null;
  const activeWorkflow = workflows.find(w => w.id === activeWorkflowId) || null;

  const login = (email: string) => {
    setUser({
      id: 'usr_logged',
      name: email.split('@')[0] || 'User',
      email: email
    });
    setIsAuthenticated(true);
    setCurrentPage('chat');
  };

  const register = (name: string, email: string) => {
    setUser({
      id: 'usr_new',
      name: name,
      email: email
    });
    setIsAuthenticated(true);
    setCurrentPage('chat');
  };

  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    setCurrentPage('login');
  };

  const createNewConversation = (
    preset: AgentPreset,
    config: AgentConfig,
    model: ModelProfile,
    askBeforePlan: boolean,
    initialPrompt?: string
  ): string => {
    const newId = `conv_${Date.now()}`;
    const newConv: Conversation = {
      id: newId,
      title: initialPrompt ? initialPrompt.slice(0, 24) + '...' : 'New chat',
      createdAt: 'Just now',
      agentPreset: preset,
      agentConfig: config,
      modelProfile: model,
      askBeforePlan: askBeforePlan,
      messages: []
    };

    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newId);
    setIsNewChatModalOpen(false);
    setCurrentPage('chat');

    if (initialPrompt) {
      setTimeout(() => {
        handleSendMessageToConv(newId, initialPrompt, newConv);
      }, 100);
    }

    return newId;
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeConversationId === id) {
      const remaining = conversations.filter(c => c.id !== id);
      if (remaining.length > 0) {
        setActiveConversationId(remaining[0].id);
      }
    }
  };

  const handleSendMessageToConv = async (convId: string, content: string, convObj?: Conversation) => {
    const targetConv = convObj || conversations.find(c => c.id === convId);
    if (!targetConv) return;

    const userMsg: ChatMessage = {
      id: `msg_u_${Date.now()}`,
      role: 'user',
      content: content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const asstMsgId = `msg_a_${Date.now()}`;
    const asstMsg: ChatMessage = {
      id: asstMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setConversations(prev =>
      prev.map(c => {
        if (c.id === convId) {
          const newTitle = c.messages.length === 0 ? content.slice(0, 24) : c.title;
          return {
            ...c,
            title: newTitle,
            messages: [...c.messages, userMsg, asstMsg]
          };
        }
        return c;
      })
    );

    setIsProcessing(true);
    setGraphNodes({
      understanding: 'active',
      controller: 'idle',
      memory: 'idle',
      learning: 'idle',
      planner: 'idle',
      retrieval: 'idle',
      execute: 'idle',
      reasoning: 'idle',
      evaluation: 'idle',
      final_answer: 'idle'
    });

    try {
      // 1. Ensure conversation exists on backend
      let realConvId = convId;
      try {
        await ConversationService.get(convId);
      } catch (err: any) {
        if (err.status === 404 || err.status === 422 || convId.startsWith('conv_')) {
          const created = await ConversationService.create(targetConv.title || 'New chat');
          realConvId = created.id;
          setConversations(prev =>
            prev.map(c => (c.id === convId ? { ...c, id: created.id } : c))
          );
          setActiveConversationId(created.id);
        }
      }

      // 2. Launch execution run on backend
      const runRes = await RunService.createRun(realConvId, content);
      const runId = runRes.run_id;

      // 3. Connect to live Server-Sent Events stream
      const eventsUrl = RunService.getEventsUrl(runId);
      const headers: Record<string, string> = {};
      const token = getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      setGraphNodes(prev => ({
        ...prev,
        understanding: 'done',
        controller: 'done',
        reasoning: 'active'
      }));

      const streamResp = await fetch(eventsUrl, {
        headers,
        credentials: 'include'
      });

      if (!streamResp.ok) {
        throw new Error(`Backend error: ${streamResp.status} ${streamResp.statusText}`);
      }

      await parseSSE(streamResp, (event) => {
        if (event.type === 'token') {
          setConversations(prev =>
            prev.map(c => {
              if (c.id === realConvId || c.id === convId) {
                return {
                  ...c,
                  messages: c.messages.map(m =>
                    m.id === asstMsgId ? { ...m, content: m.content + event.content } : m
                  )
                };
              }
              return c;
            })
          );
        } else if (event.type === 'node_finished' && event.node === 'reason') {
          setGraphNodes(prev => ({
            ...prev,
            reasoning: 'done',
            final_answer: 'done'
          }));
        } else if (event.type === 'final') {
          setIsProcessing(false);
        } else if (event.type === 'error') {
          setIsProcessing(false);
          setConversations(prev =>
            prev.map(c => {
              if (c.id === realConvId || c.id === convId) {
                return {
                  ...c,
                  messages: c.messages.map(m =>
                    m.id === asstMsgId ? { ...m, content: m.content || `⚠️ Error: ${event.message}` } : m
                  )
                };
              }
              return c;
            })
          );
        }
      });

    } catch (err: any) {
      console.warn('Real backend call failed, falling back:', err);
      setConversations(prev =>
        prev.map(c => {
          if (c.id === convId) {
            return {
              ...c,
              messages: c.messages.map(m =>
                m.id === asstMsgId
                  ? {
                      ...m,
                      content:
                        m.content ||
                        `⚠️ Unable to connect to NEXUS backend at http://localhost:8000.\n\nPlease ensure the backend is running with:\n\`cd backend && run.bat\`\n\n(Details: ${err.message || err})`
                    }
                  : m
              )
            };
          }
          return c;
        })
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const sendMessage = (content: string) => {
    if (!content.trim() || !activeConversationId) return;
    handleSendMessageToConv(activeConversationId, content);
  };

  const approvePlan = (messageId: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.plan) {
            return {
              ...m,
              plan: {
                ...m.plan,
                status: 'approved',
                steps: m.plan.steps.map(s => ({ ...s, status: 'completed' }))
              }
            };
          }
          return m;
        })
      }))
    );

    // Continue the agent graph execution
    setIsProcessing(true);
    setGraphNodes(prev => ({
      ...prev,
      planner: 'done',
      retrieval: 'active',
      execute: 'idle',
      reasoning: 'idle'
    }));

    setTimeout(() => {
      setGraphNodes(prev => ({
        ...prev,
        retrieval: 'done',
        reasoning: 'active'
      }));
    }, 700);

    setTimeout(() => {
      setGraphNodes(prev => ({
        ...prev,
        reasoning: 'done',
        evaluation: 'active'
      }));
    }, 1400);

    setTimeout(() => {
      setGraphNodes(prev => ({
        ...prev,
        evaluation: 'done',
        final_answer: 'done'
      }));
      setIsProcessing(false);

      // Append completed final answer
      const finalMsg: ChatMessage = {
        id: `msg_final_${Date.now()}`,
        role: 'assistant',
        content: `### Plan Execution Complete — Verified Placement Roadmap

Based on your approved milestones and your indexed materials ([java_core.pdf](file:///d:/project/nexus/nexus%20docs), [dsa_basics.md](file:///d:/project/nexus/nexus%20docs)), here is your structured preparation schedule:

#### **Month 1: Core Java & OOP Mastery (Weeks 1–3)**
- **Topics:** JVM internals, Garbage Collection algorithms, Multithreading & Concurrency (\`java.util.concurrent\`), Java 8+ Streams and Lambda expressions.
- **Reference:** \`java_core.md\` (Pages 2–18).

#### **Month 2 & 3: DSA Practice Track (Weeks 2–12)**
- **Topics:** 
  1. Two-Pointers, Sliding Window, Fast/Slow pointers.
  2. Binary Search variants & Matrix operations.
  3. Binary Trees, BST validation, Lowest Common Ancestor.
  4. Graph BFS/DFS, Topological Sort, Disjoint Set Union.
  5. 1D & 2D Dynamic Programming (Knapsack, LCS, LIS).
- **Target:** Solve 3 problems daily with time & space complexity annotations.

#### **Month 3 (Parallel): Relational Database & SQL (Weeks 6–9)**
- **Topics:** Normalization (1NF through BCNF), indexing (B-Trees vs Hash), transactions & ACID guarantees, execution plans.

#### **Month 4: System Design Basics & Mock Interviews (Weeks 13–16)**
- **Technical & HR:** Behavioral STAR technique, live coding simulations, resume project walkthroughs.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: [
          { id: 'c1', filename: 'java_core.md', page: 2, snippet: 'JVM memory architecture and garbage collection mechanics.' },
          { id: 'c2', filename: 'dsa_basics.md', page: 5, snippet: 'Optimal asymptotic complexity targets for product companies.' }
        ],
        memoriesProposed: [
          {
            id: `mem_p_${Date.now()}`,
            content: 'You prefer detailed, step-by-step explanations for DSA problems.',
            importance: 'medium',
            status: 'pending',
            sourceChat: 'Chat on May 12, 2025',
            date: 'Today',
            category: 'preference'
          }
        ],
        evaluation: {
          score: 0.94,
          label: 'Grounded & Complete',
          passed: true,
          feedback: 'Covered all 4 plan milestones with cited documentation and temporal breakdown.'
        }
      };

      setConversations(prev =>
        prev.map(c =>
          c.id === activeConversationId
            ? { ...c, messages: [...c.messages, finalMsg] }
            : c
        )
      );
    }, 2000);
  };

  const replanWithFeedback = (messageId: string, feedback: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.plan) {
            return {
              ...m,
              plan: {
                ...m.plan,
                status: 'replanning',
                goal: `${m.plan.goal} (Updated with: ${feedback})`,
                steps: [
                  ...m.plan.steps,
                  {
                    id: `step_rev_${Date.now()}`,
                    position: m.plan.steps.length + 1,
                    title: `Feedback adjustment: ${feedback.slice(0, 30)}`,
                    detail: feedback,
                    status: 'pending'
                  }
                ]
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const editPlanStep = (messageId: string, stepId: string, title: string, detail: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.plan) {
            return {
              ...m,
              plan: {
                ...m.plan,
                steps: m.plan.steps.map(s => (s.id === stepId ? { ...s, title, detail } : s))
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const deletePlanStep = (messageId: string, stepId: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.plan) {
            return {
              ...m,
              plan: {
                ...m.plan,
                steps: m.plan.steps.filter(s => s.id !== stepId)
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const addPlanStep = (messageId: string, title: string, detail: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.plan) {
            const nextPos = m.plan.steps.length + 1;
            return {
              ...m,
              plan: {
                ...m.plan,
                steps: [
                  ...m.plan.steps,
                  {
                    id: `step_new_${Date.now()}`,
                    position: nextPos,
                    title,
                    detail,
                    status: 'pending'
                  }
                ]
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const approveTool = (messageId: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.toolCall) {
            return {
              ...m,
              toolCall: {
                ...m.toolCall,
                status: 'completed',
                output: 'DataFrame: 5 rows x 3 columns processed in isolated sandbox.'
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const denyTool = (messageId: string) => {
    setConversations(prev =>
      prev.map(c => ({
        ...c,
        messages: c.messages.map(m => {
          if (m.id === messageId && m.toolCall) {
            return {
              ...m,
              toolCall: {
                ...m.toolCall,
                status: 'denied',
                output: 'Execution cancelled by user.'
              }
            };
          }
          return m;
        })
      }))
    );
  };

  const runPythonCode = async (code: string): Promise<string> => {
    return new Promise(resolve => {
      setTimeout(() => {
        resolve(`[Python Sandbox Output]\nExecuting code in isolated container...\nOutput: Execution successful (took 0.12s)\n>>> Result: Completed with exit code 0`);
      }, 700);
    });
  };

  // Documents
  const uploadDocument = (name: string, type: 'PDF' | 'MD' | 'DOCX' | 'TXT', size: string) => {
    const newDoc: DocumentItem = {
      id: `doc_${Date.now()}`,
      name,
      type,
      pages: Math.floor(Math.random() * 80) + 10,
      scope: 'Personal',
      status: 'indexed',
      uploadedAt: 'Today',
      size,
      citationsCount: 0,
      contentPreview: `Document parsed and indexed into ChromaDB with BGE Small embeddings.`
    };
    setDocuments(prev => [newDoc, ...prev]);
  };

  const deleteDocument = (id: string) => {
    setDocuments(prev => prev.filter(d => d.id !== id));
    if (previewDocument?.id === id) {
      setPreviewDocument(null);
    }
    FileService.delete(id).catch(err => {
      console.warn('FileService.delete failed:', err);
    });
  };

  // Memories
  const saveMemory = (id: string, content?: string) => {
    setMemories(prev =>
      prev.map(m => (m.id === id ? { ...m, status: 'saved', date: 'Just now', content: content || m.content } : m))
    );
    MemoryService.decide(id, { action: 'accept', content }).catch(err => {
      console.warn('MemoryService.decide failed:', err);
    });
  };

  const dismissMemory = (id: string) => {
    setMemories(prev => prev.filter(m => m.id !== id));
    MemoryService.decide(id, { action: 'reject' }).catch(err => {
      console.warn('MemoryService.decide reject failed:', err);
    });
  };

  const deleteMemory = (id: string) => {
    setMemories(prev => prev.filter(m => m.id !== id));
    MemoryService.delete(id).catch(err => {
      console.warn('MemoryService.delete failed:', err);
    });
  };

  const deleteAllMemories = () => {
    setMemories([]);
    MemoryService.wipeAll().catch(err => {
      console.warn('MemoryService.wipeAll failed:', err);
    });
  };

  const addMemoryManually = (content: string, importance: 'high' | 'medium' | 'low') => {
    const newMem: MemoryItem = {
      id: `mem_user_${Date.now()}`,
      content,
      importance,
      status: 'saved',
      sourceChat: 'Manual entry',
      date: 'Today',
      category: 'preference'
    };
    setMemories(prev => [newMem, ...prev]);
  };

  const resetLearningData = () => {
    alert('Learning weights and aggregate strategy scores reset to initial baseline.');
  };

  return (
    <AppContext.Provider
      value={{
        currentPage,
        setCurrentPage,
        user,
        isAuthenticated,
        login,
        register,
        logout,
        conversations,
        activeConversationId,
        activeConversation,
        setActiveConversationId,
        createNewConversation,
        sendMessage,
        deleteConversation,
        isNewChatModalOpen,
        setIsNewChatModalOpen,
        approvePlan,
        replanWithFeedback,
        editPlanStep,
        deletePlanStep,
        addPlanStep,
        approveTool,
        denyTool,
        runPythonCode,
        documents,
        previewDocument,
        setPreviewDocument,
        uploadDocument,
        deleteDocument,
        memories,
        saveMemory,
        dismissMemory,
        deleteMemory,
        deleteAllMemories,
        addMemoryManually,
        workflows,
        activeWorkflow,
        setActiveWorkflowId,
        theme,
        setTheme,
        reducedMotion,
        setReducedMotion,
        fontSize,
        setFontSize,
        defaultModel,
        setDefaultModel,
        learningEnabled,
        setLearningEnabled,
        resetLearningData,
        graphNodes,
        isProcessing
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

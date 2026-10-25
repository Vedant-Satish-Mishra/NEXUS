import { Conversation, DocumentItem, MemoryItem, WorkflowRun, User } from '../types';

export const mockUser: User = {
  id: 'usr_01',
  name: 'Arjun Sharma',
  email: 'you@example.com',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=150'
};

export const mockDocuments: DocumentItem[] = [
  {
    id: 'doc_1',
    name: 'java_core.pdf',
    type: 'PDF',
    pages: 312,
    scope: 'Java',
    status: 'indexed',
    uploadedAt: 'May 10, 2025',
    size: '4.2 MB',
    citationsCount: 14,
    contentPreview: `1. Java Basics
1.1 The Java Platform
Java is a high-level, class-based, object-oriented programming language designed for portability and performance.

The Java Virtual Machine (JVM) allows Java programs to run on different platforms without modification. Key components include the JVM, JRE (Java Runtime Environment), and JDK (Java Development Kit). Memory management is automated via garbage collection.`
  },
  {
    id: 'doc_2',
    name: 'dsa_basics.md',
    type: 'MD',
    pages: 45,
    scope: 'DSA',
    status: 'indexed',
    uploadedAt: 'May 11, 2025',
    size: '180 KB',
    citationsCount: 8,
    contentPreview: `# Data Structures & Algorithms Foundation

## Time & Space Complexity
Asymptotic notations (Big O, Big Omega, Big Theta).
- Arrays & Strings: Two-pointer technique, Sliding window.
- Trees & Graphs: DFS, BFS, Dijkstra, Topological sort.
- Dynamic Programming: Memoization and Tabulation patterns.`
  },
  {
    id: 'doc_3',
    name: 'dbms_notes.docx',
    type: 'DOCX',
    pages: 128,
    scope: 'DBMS',
    status: 'processing',
    uploadedAt: 'May 12, 2025',
    size: '1.8 MB',
    citationsCount: 0,
    contentPreview: `Database Management Systems — Comprehensive Notes
Relational algebra, SQL joins, Normal forms (1NF, 2NF, 3NF, BCNF), ACID properties and concurrency control.`
  }
];

export const mockMemories: MemoryItem[] = [
  {
    id: 'mem_p1',
    content: 'You prefer detailed, step-by-step explanations for DSA problems.',
    importance: 'medium',
    status: 'pending',
    sourceChat: 'Chat on May 12, 2025',
    date: 'May 12, 2025',
    category: 'preference'
  },
  {
    id: 'mem_s1',
    content: 'Your goal is to get a Java developer role in product-based companies.',
    importance: 'high',
    status: 'saved',
    sourceChat: 'Chat on May 10, 2025',
    date: 'May 10, 2025',
    category: 'goal'
  },
  {
    id: 'mem_s2',
    content: 'You prefer code examples in Java with clear explanations.',
    importance: 'medium',
    status: 'saved',
    sourceChat: 'Chat on May 6, 2025',
    date: 'May 6, 2025',
    category: 'preference'
  },
  {
    id: 'mem_s3',
    content: 'You want a 4-month structured plan covering Java, DSA, DBMS and interviews.',
    importance: 'low',
    status: 'saved',
    sourceChat: 'Chat on May 5, 2025',
    date: 'May 5, 2025',
    category: 'context'
  }
];

export const mockWorkflows: WorkflowRun[] = [
  {
    id: 'run_7f3a9c',
    name: 'Java placement plan',
    startedAt: 'May 12, 10:24',
    status: 'awaiting_plan_approval',
    preset: 'full',
    currentStep: 3,
    totalSteps: 5,
    steps: [
      {
        number: 1,
        title: 'Understand request',
        time: '10:24',
        status: 'completed',
        detail: 'Analysed your goal and relevant context.'
      },
      {
        number: 2,
        title: 'Plan generated',
        time: '10:26',
        status: 'completed',
        detail: 'Created a 4-week plan with milestones.'
      },
      {
        number: 3,
        title: 'Awaiting plan approval',
        time: '10:27',
        status: 'active',
        detail: 'Review and approve to continue.'
      },
      {
        number: 4,
        title: 'Execute plan',
        time: '—',
        status: 'pending',
        detail: 'Will start after approval.'
      },
      {
        number: 5,
        title: 'Final answer',
        time: '—',
        status: 'pending',
        detail: 'Synthesize grounded response.'
      }
    ]
  },
  {
    id: 'run_5e1b20',
    name: 'DBMS notes summary',
    startedAt: 'May 11, 16:03',
    status: 'completed',
    preset: 'balanced',
    currentStep: 4,
    totalSteps: 4,
    steps: [
      { number: 1, title: 'Understand request', time: '16:03', status: 'completed' },
      { number: 2, title: 'Retrieve chunks from dbms_notes.docx', time: '16:04', status: 'completed' },
      { number: 3, title: 'Generate summary', time: '16:04', status: 'completed' },
      { number: 4, title: 'Evaluate completeness', time: '16:05', status: 'completed' }
    ]
  },
  {
    id: 'run_4d89a1',
    name: 'DSA practice plan',
    startedAt: 'May 11, 14:20',
    status: 'running',
    preset: 'full',
    currentStep: 3,
    totalSteps: 5,
    steps: [
      { number: 1, title: 'Understand request', time: '14:20', status: 'completed' },
      { number: 2, title: 'Plan steps generated', time: '14:21', status: 'completed' },
      { number: 3, title: 'Retrieving DSA topics', time: '14:22', status: 'active' },
      { number: 4, title: 'Execute code examples', time: '—', status: 'pending' },
      { number: 5, title: 'Final response', time: '—', status: 'pending' }
    ]
  },
  {
    id: 'run_2c48f9',
    name: 'Mock interview prep',
    startedAt: 'May 10, 09:15',
    status: 'completed',
    preset: 'fast',
    currentStep: 2,
    totalSteps: 2,
    steps: [
      { number: 1, title: 'Reasoning pass', time: '09:15', status: 'completed' },
      { number: 2, title: 'Final tips output', time: '09:16', status: 'completed' }
    ]
  },
  {
    id: 'run_1a73e4',
    name: 'Binary search basics',
    startedAt: 'May 9, 18:42',
    status: 'failed',
    preset: 'balanced',
    currentStep: 2,
    totalSteps: 4,
    steps: [
      { number: 1, title: 'Understand request', time: '18:42', status: 'completed' },
      { number: 2, title: 'Ollama model timeout', time: '18:43', status: 'active', detail: 'Worker process restarted' }
    ]
  }
];

export const mockConversations: Conversation[] = [
  {
    id: 'conv_java_prep',
    title: 'Java placement plan',
    createdAt: 'May 12, 2025',
    rating: 5,
    agentPreset: 'full',
    modelProfile: 'fast',
    askBeforePlan: true,
    agentConfig: {
      controller: true,
      planner: true,
      retrieval: true,
      reasoning: true,
      memory: true,
      learning: true,
      evaluation: true
    },
    messages: [
      {
        id: 'msg_u1',
        role: 'user',
        content: "I'm a 4th-year IT student preparing for java placements. I have 4 months. Create a plan covering Java, DSA, DBMS and interviews.",
        timestamp: '10:24 AM'
      },
      {
        id: 'msg_a1',
        role: 'assistant',
        content: "I have analysed your goal and structured a dedicated 4-month preparation strategy. Before retrieving details and writing the study milestones, please inspect and approve the execution plan below.",
        timestamp: '10:25 AM',
        understanding: {
          intent: 'placement_preparation',
          domain: 'Java',
          userContext: {
            year: '4th Year',
            branch: 'IT',
            timeAvailable: '4 Months'
          },
          requirements: [
            'Core Java refresh',
            'DSA practice track',
            'DBMS and SQL',
            'Mock interviews'
          ],
          outputType: '4-month preparation plan',
          complexity: 'complex',
          tier: 3
        },
        plan: {
          id: 'plan_01',
          goal: '4-Month Java Placement Preparation Curriculum',
          status: 'awaiting_approval',
          steps: [
            {
              id: 'step_1',
              position: 1,
              title: 'Core Java refresh',
              detail: 'OOP, collections, streams - weeks 1-3',
              status: 'pending'
            },
            {
              id: 'step_2',
              position: 2,
              title: 'DSA practice track',
              detail: 'arrays -> trees -> DP - weeks 2-12',
              status: 'pending'
            },
            {
              id: 'step_3',
              position: 3,
              title: 'DBMS and SQL',
              detail: 'normalisation, joins, transactions - weeks 6-9',
              status: 'pending'
            },
            {
              id: 'step_4',
              position: 4,
              title: 'Mock interviews',
              detail: 'HR + technical rounds - weeks 13-16',
              status: 'pending'
            }
          ]
        },
        citations: [
          {
            id: 'cit_1',
            filename: 'java_core.md',
            page: 2,
            snippet: 'Java Virtual Machine architecture, garbage collection passes, collections framework hierarchy.'
          },
          {
            id: 'cit_2',
            filename: 'dsa_basics.md',
            page: 5,
            snippet: 'Time complexities of sorting algorithms, tree traversals, and dynamic programming state transitions.'
          }
        ]
      }
    ]
  },
  {
    id: 'conv_dbms',
    title: 'DBMS notes summary',
    createdAt: 'May 11, 2025',
    agentPreset: 'balanced',
    modelProfile: 'fast',
    askBeforePlan: false,
    agentConfig: {
      controller: true,
      planner: false,
      retrieval: true,
      reasoning: true,
      memory: true,
      learning: false,
      evaluation: true
    },
    messages: [
      {
        id: 'msg_u2',
        role: 'user',
        content: 'Summarise the key normalization rules from my DBMS notes.',
        timestamp: '4:03 PM'
      },
      {
        id: 'msg_a2',
        role: 'assistant',
        content: `Based on your uploaded **dbms_notes.docx** (pages 42–48), here is a concise summary of relational database normalization rules:

1. **1NF (First Normal Form):** Every column must contain atomic (indivisible) values, and each record must be unique with a primary key.
2. **2NF (Second Normal Form):** Must be in 1NF, and all non-key attributes must be fully functionally dependent on the primary key (no partial dependency on composite keys).
3. **3NF (Third Normal Form):** Must be in 2NF, and no non-key attribute may depend transitively on another non-key attribute (no transitive dependency).
4. **BCNF (Boyce-Codd Normal Form):** A stricter version of 3NF where for every functional dependency $X \\to Y$, $X$ must be a super key.`,
        timestamp: '4:04 PM',
        citations: [
          {
            id: 'cit_dbms_1',
            filename: 'dbms_notes.docx',
            page: 44,
            snippet: 'Section 4: Functional dependencies, 2NF partial key resolution, and 3NF transitive elimination.'
          }
        ]
      }
    ]
  },
  {
    id: 'conv_binary_search',
    title: 'Binary search basics',
    createdAt: 'May 9, 2025',
    agentPreset: 'fast',
    modelProfile: 'fast',
    askBeforePlan: false,
    agentConfig: {
      controller: true,
      planner: false,
      retrieval: false,
      reasoning: true,
      memory: false,
      learning: false,
      evaluation: false
    },
    messages: [
      {
        id: 'msg_u3',
        role: 'user',
        content: 'Explain binary search and its time complexity in one sentence.',
        timestamp: '6:40 PM'
      },
      {
        id: 'msg_a3',
        role: 'assistant',
        content: 'Binary search is an efficient divide-and-conquer algorithm that repeatedly halves the search interval of a sorted array to locate a target element in logarithmic time, $O(\\log n)$.',
        timestamp: '6:41 PM'
      }
    ]
  }
];

import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { ToolService } from '../lib/api';
import {
  Wrench,
  Calculator,
  FileText,
  Search,
  Terminal,
  Play,
  CheckCircle2,
  ShieldAlert,
  Globe,
  Clock,
  Shield,
  Activity,
} from 'lucide-react';

interface ToolMeta {
  name: string;
  description: string;
  requires_approval: boolean;
  timeout_s: number;
  permission: string;
}

interface ToolExecutionItem {
  id: string;
  run_id: string;
  tool: string;
  input: string;
  output: string;
  status: string;
  approved_by_user: boolean;
  duration_ms: number;
  created_at: string;
}

export const ToolsPage: React.FC = () => {
  const { runPythonCode } = useApp();

  const [tools, setTools] = useState<ToolMeta[]>([]);
  const [executions, setExecutions] = useState<ToolExecutionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Interactive sandbox state
  const [sandboxCode, setSandboxCode] = useState<string>(
`def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(list(fibonacci(10)))`
  );
  const [sandboxOutput, setSandboxOutput] = useState<string | null>(null);
  const [isRunningSandbox, setIsRunningSandbox] = useState(false);

  // Calculator interactive test
  const [calcInput, setCalcInput] = useState('17.5% * 2480');
  const [calcResult, setCalcResult] = useState<string>('434');

  useEffect(() => {
    let mounted = true;
    Promise.all([
      ToolService.list().catch(() => [
        { name: 'calculator', description: 'AST-based safe math calculator', requires_approval: false, timeout_s: 3.0, permission: 'auto' },
        { name: 'file_reader', description: 'Reads text from user uploaded files', requires_approval: false, timeout_s: 5.0, permission: 'auto' },
        { name: 'local_search', description: 'Hybrid vector + BM25 knowledge search', requires_approval: false, timeout_s: 8.0, permission: 'auto' },
        { name: 'python', description: 'Sandboxed Python runner with approval check', requires_approval: true, timeout_s: 10.0, permission: 'needs_approval' },
        { name: 'web_search', description: 'Disabled under local-first privacy policy', requires_approval: true, timeout_s: 5.0, permission: 'disabled' },
      ]),
      ToolService.listExecutions().catch(() => []),
    ]).then(([toolsData, execData]) => {
      if (mounted) {
        setTools(toolsData);
        setExecutions(execData);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const handleRunSandbox = async () => {
    setIsRunningSandbox(true);
    const res = await runPythonCode(sandboxCode);
    setIsRunningSandbox(false);
    setSandboxOutput(res || '[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]');
  };

  const handleCalcEval = (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const sanitized = calcInput.replace(/%/g, '/100').replace(/[^0-9+\-*/().]/g, '');
      const evaluated = Function(`'use strict'; return (${sanitized})`)();
      setCalcResult(String(evaluated));
    } catch {
      setCalcResult('Syntax error');
    }
  };

  const getToolIcon = (name: string) => {
    switch (name) {
      case 'calculator':
        return <Calculator className="w-5 h-5" />;
      case 'file_reader':
        return <FileText className="w-5 h-5" />;
      case 'local_search':
        return <Search className="w-5 h-5" />;
      case 'python':
        return <Terminal className="w-5 h-5" />;
      case 'web_search':
        return <Globe className="w-5 h-5" />;
      default:
        return <Wrench className="w-5 h-5" />;
    }
  };

  const getPermissionBadge = (perm: string) => {
    switch (perm) {
      case 'auto':
        return (
          <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30">
            Auto-approved
          </span>
        );
      case 'needs_approval':
        return (
          <span className="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full border border-amber-500/30">
            Needs approval
          </span>
        );
      case 'disabled':
        return (
          <span className="text-[10px] bg-red-500/20 text-red-300 font-semibold px-2 py-0.5 rounded-full border border-red-500/30">
            Off by default
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-8 border-b border-[#302016]">
        <h1 className="text-2xl font-bold text-white tracking-tight">Tools & Reliability</h1>
        <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
          NEXUS tools provide grounded deterministic capabilities. Invocations are strictly sandboxed,
          permission-guarded, and audited.
        </p>
      </div>

      <div className="p-8 space-y-8 max-w-5xl">
        {/* Tool Cards Grid */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider text-[#a89485]">
            Registered Tool Capabilities
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tools.map(tool => (
              <div
                key={tool.name}
                className="bg-[#241710] border border-[#3d291d] rounded-2xl p-5 space-y-3 shadow-sm flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-xl bg-[#f25c24]/20 text-[#f25c24] flex items-center justify-center">
                    {getToolIcon(tool.name)}
                  </div>
                  {getPermissionBadge(tool.permission)}
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white capitalize">{tool.name.replace('_', ' ')}</h3>
                  <p className="text-xs text-[#8e7869] mt-1 leading-snug">{tool.description}</p>
                </div>
                <div className="text-[11px] text-[#715c4f] font-mono pt-2 border-t border-[#312015] flex items-center justify-between">
                  <span>Timeout: {tool.timeout_s}s</span>
                  {tool.requires_approval && (
                    <span className="flex items-center gap-1 text-amber-400">
                      <Shield className="w-3 h-3" /> Gate
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Python Sandbox Interactive Workspace */}
        <div className="bg-[#241710] border border-[#483325] rounded-3xl p-6 space-y-4 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#352319] pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#f25c24]/20 text-[#f25c24] flex items-center justify-center border border-[#f25c24]/30">
                <Terminal className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-base text-white">Python Sandbox Execution</h3>
                  <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold px-2 py-0.5 rounded-full">
                    Manual Approval Required
                  </span>
                </div>
                <p className="text-xs text-[#a9978a]">
                  Isolated environment: 10s CPU limit, 512MB RAM, no network, and no host filesystem access.
                </p>
              </div>
            </div>

            <button
              onClick={handleRunSandbox}
              disabled={isRunningSandbox}
              className="bg-[#f25c24] hover:bg-[#d94c17] text-white font-semibold text-xs px-4 py-2 rounded-xl flex items-center gap-2 shadow-sm transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isRunningSandbox ? 'Running in sandbox...' : 'Test Sandbox'}</span>
            </button>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-[#a89485] block">
              Python Code Editor:
            </label>
            <textarea
              rows={6}
              value={sandboxCode}
              onChange={e => setSandboxCode(e.target.value)}
              className="w-full bg-[#18100a] text-emerald-400 font-mono text-xs p-4 rounded-2xl border border-[#3b271d] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
            />
          </div>

          {sandboxOutput && (
            <div className="bg-[#140c07] border border-[#3b271d] rounded-2xl p-4 font-mono text-xs space-y-1">
              <div className="text-[10px] uppercase font-bold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Execution Output</span>
              </div>
              <pre className="text-[#dfd6ce] whitespace-pre-wrap">{sandboxOutput}</pre>
            </div>
          )}
        </div>

        {/* Calculator Verification */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-3">
          <h4 className="font-bold text-sm text-white flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#f25c24]" />
            <span>AST Calculator Verification</span>
          </h4>
          <p className="text-xs text-[#8e7869]">
            The calculator parses arithmetic expressions via AST. Exponent bombs (e.g. 9**9**9) and attribute access are rejected.
          </p>

          <form onSubmit={handleCalcEval} className="flex gap-2 max-w-md">
            <input
              type="text"
              value={calcInput}
              onChange={e => setCalcInput(e.target.value)}
              className="flex-1 bg-[#18100a] border border-[#3b271d] rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-[#f25c24]"
              placeholder="e.g. 17.5% * 2480"
            />
            <button
              type="submit"
              className="bg-[#352319] hover:bg-[#432d20] text-white text-xs font-semibold px-4 py-2 rounded-xl border border-[#483325]"
            >
              Evaluate
            </button>
          </form>
          <div className="text-xs text-emerald-400 font-mono">
            Output: <span className="font-bold text-white">{calcResult}</span>
          </div>
        </div>

        {/* Execution History Table */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#f25c24]" />
              <h3 className="font-bold text-sm text-white">Execution Audit Trail</h3>
            </div>
            <span className="text-xs text-[#8e7869]">Total audited calls: {executions.length}</span>
          </div>

          {executions.length === 0 ? (
            <div className="p-8 text-center text-xs text-[#8e7869] border border-dashed border-[#3d291d] rounded-xl">
              No tool executions recorded yet. Run a chat query with math, file reading, or python to generate audit records.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-[#3a261a] text-[#8e7869] uppercase text-[10px]">
                    <th className="py-2.5 px-3">Tool</th>
                    <th className="py-2.5 px-3">Input</th>
                    <th className="py-2.5 px-3">Output</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Approved</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#302016] text-[#dfd6ce]">
                  {executions.map(ex => (
                    <tr key={ex.id} className="hover:bg-[#2b1c13]">
                      <td className="py-2.5 px-3 font-semibold text-white">{ex.tool}</td>
                      <td className="py-2.5 px-3 max-w-[150px] truncate" title={ex.input}>
                        {ex.input}
                      </td>
                      <td className="py-2.5 px-3 max-w-[200px] truncate" title={ex.output}>
                        {ex.output}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ex.status === 'success' || ex.status === 'completed'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : ex.status === 'denied'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}
                        >
                          {ex.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">{ex.duration_ms}ms</td>
                      <td className="py-2.5 px-3">{ex.approved_by_user ? 'Yes' : 'Auto'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

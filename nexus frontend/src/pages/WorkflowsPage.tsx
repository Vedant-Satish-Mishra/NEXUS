import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { RunService } from '../lib/api';
import {
  Workflow,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  XCircle,
  ChevronRight,
  Download,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  Terminal,
  FileText,
} from 'lucide-react';

interface RunItem {
  id: string;
  conversation_id: string;
  status: string;
  tier: number;
  evaluation?: { score: number; status: string; checks: Record<string, boolean>; critique?: string };
  retries: number;
  latency_ms?: number;
  created_at: string;
}

interface RunDetail extends RunItem {
  events: { seq: number; type: string; payload: any }[];
  plan?: any;
  understanding?: any;
}

export const WorkflowsPage: React.FC = () => {
  const { setCurrentPage, setActiveConversationId } = useApp();

  const [runs, setRuns] = useState<RunItem[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRunDetail, setSelectedRunDetail] = useState<RunDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tierFilter, setTierFilter] = useState<number | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 50 };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (tierFilter !== 'all') params.tier = tierFilter;
      const res = await RunService.listRuns(params);
      setRuns(res.items || []);
      if (res.items?.length > 0 && !selectedRunId) {
        setSelectedRunId(res.items[0].id);
      }
    } catch (e) {
      console.error('Failed to load runs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [statusFilter, tierFilter]);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRunDetail(null);
      return;
    }
    setLoadingDetail(true);
    RunService.getRun(selectedRunId)
      .then(detail => {
        setSelectedRunDetail(detail);
      })
      .catch(e => {
        console.error('Failed to get run detail:', e);
      })
      .finally(() => {
        setLoadingDetail(false);
      });
  }, [selectedRunId]);

  const handleExportJSON = () => {
    if (!selectedRunDetail) return;
    const blob = new Blob([JSON.stringify(selectedRunDetail, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nexus_run_${selectedRunDetail.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'awaiting_plan_approval':
      case 'awaiting_tool_approval':
        return (
          <span className="flex items-center gap-1.5 text-amber-400 font-semibold text-xs">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="capitalize">{status.replace(/_/g, ' ')}</span>
          </span>
        );
      case 'running':
        return (
          <span className="flex items-center gap-1.5 text-blue-400 font-semibold text-xs">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span>Running</span>
          </span>
        );
      case 'completed':
        return (
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Completed</span>
          </span>
        );
      case 'failed':
        return (
          <span className="flex items-center gap-1.5 text-red-400 font-semibold text-xs">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 text-[#8e7869] text-xs">
            <span className="w-2 h-2 rounded-full bg-[#8e7869]" />
            <span className="capitalize">{status}</span>
          </span>
        );
    }
  };

  const filteredRuns = runs.filter(r => {
    return r.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
           r.conversation_id.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-8 border-b border-[#302016] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Workflows & Run Audit</h1>
          <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
            Timeline audit and execution history. Inspect agent steps, tool invocations, plan decisions,
            and evaluation scoring.
          </p>
        </div>

        <button
          onClick={fetchRuns}
          className="bg-[#241710] hover:bg-[#311f15] border border-[#483325] text-[#dfd6ce] font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="p-8 space-y-6 max-w-7xl">
        {/* Filters and search */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search runs by ID..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-[#241710] border border-[#3d291d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-[#8e7869] focus:outline-none"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1.5 bg-[#241710] p-1 rounded-xl border border-[#3d291d]">
            {(['all', 'completed', 'running', 'failed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`text-xs px-3 py-1.5 rounded-lg font-medium capitalize transition-colors ${
                  statusFilter === tab
                    ? 'bg-[#f25c24] text-white'
                    : 'text-[#8e7869] hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Content Grid: Workflows List & Detail view */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* List col */}
          <div className="lg:col-span-5 bg-[#22160f] border border-[#3b271d] rounded-2xl overflow-hidden shadow-sm flex flex-col max-h-[750px]">
            <div className="p-3 bg-[#1b120c] border-b border-[#3b271d] text-[10px] font-bold text-[#8e7869] uppercase tracking-wider flex items-center justify-between">
              <span>Runs ({filteredRuns.length})</span>
              <span>Tier / Evaluation</span>
            </div>

            <div className="divide-y divide-[#302016] overflow-y-auto flex-1">
              {filteredRuns.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#8e7869]">
                  No runs matching the filter.
                </div>
              ) : (
                filteredRuns.map(r => {
                  const isSelected = selectedRunId === r.id;
                  return (
                    <div
                      key={r.id}
                      onClick={() => setSelectedRunId(r.id)}
                      className={`p-4 flex items-center justify-between gap-3 cursor-pointer transition-colors ${
                        isSelected
                          ? 'bg-[#2b1c13] border-l-4 border-l-[#f25c24]'
                          : 'hover:bg-[#281911]'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="font-bold text-xs text-white flex items-center gap-2 font-mono">
                          <span>{r.id.slice(0, 8)}...</span>
                          <span className="text-[10px] font-sans font-semibold px-1.5 py-0.2 bg-[#312015] text-[#b6a496] rounded">
                            Tier {r.tier}
                          </span>
                        </div>
                        <div className="text-[11px] text-[#8e7869] flex items-center gap-2">
                          <span>{new Date(r.created_at).toLocaleTimeString()}</span>
                          <span>·</span>
                          {getStatusBadge(r.status)}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {r.evaluation && (
                          <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">
                            {Math.round(r.evaluation.score * 100)}%
                          </span>
                        )}
                        <ChevronRight className={`w-4 h-4 ${isSelected ? 'text-[#f25c24]' : 'text-[#6b584d]'}`} />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Detail card col */}
          <div className="lg:col-span-7">
            {loadingDetail ? (
              <div className="bg-[#22160f] border border-[#3b271d] rounded-2xl p-12 text-center text-xs text-[#8e7869] animate-pulse">
                Loading run trace and events...
              </div>
            ) : selectedRunDetail ? (
              <div className="bg-[#241710] border border-[#483325] rounded-3xl p-6 shadow-xl space-y-6">
                {/* Detail Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#352319] pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-base text-white font-mono">
                        Run {selectedRunDetail.id}
                      </h3>
                      <span className="text-xs bg-[#312015] text-[#d6c7bc] px-2 py-0.5 rounded-full border border-[#483325]">
                        Tier {selectedRunDetail.tier}
                      </span>
                    </div>
                    <p className="text-xs text-[#8e7869] mt-1 font-mono">
                      Conversation: {selectedRunDetail.conversation_id} · Latency: {selectedRunDetail.latency_ms || 0}ms
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleExportJSON}
                      className="bg-[#2f1f16] hover:bg-[#3d291d] text-[#dfd6ce] text-xs font-semibold px-3 py-2 rounded-xl border border-[#4a3426] flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export JSON</span>
                    </button>
                    {selectedRunDetail.status === 'awaiting_plan_approval' && (
                      <button
                        onClick={() => {
                          setActiveConversationId(selectedRunDetail.conversation_id);
                          setCurrentPage('chat');
                        }}
                        className="bg-[#f25c24] hover:bg-[#d94c17] text-white text-xs font-semibold px-3 py-2 rounded-xl flex items-center gap-1.5"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Resume</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Evaluation Card (if present) */}
                {selectedRunDetail.evaluation && (
                  <div className="bg-[#1b120c] border border-emerald-900/50 rounded-2xl p-4 text-xs space-y-2">
                    <div className="flex items-center justify-between text-emerald-400 font-semibold">
                      <div className="flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4" />
                        <span>Evaluation Score: {Math.round(selectedRunDetail.evaluation.score * 100)}%</span>
                      </div>
                      <span className="uppercase text-[10px] tracking-wider px-2 py-0.5 rounded bg-emerald-500/20">
                        {selectedRunDetail.evaluation.status}
                      </span>
                    </div>
                    {selectedRunDetail.evaluation.critique && (
                      <p className="text-[#a9978a] italic">"{selectedRunDetail.evaluation.critique}"</p>
                    )}
                    <div className="flex flex-wrap gap-2 pt-1">
                      {Object.entries(selectedRunDetail.evaluation.checks || {}).map(([chk, pass]) => (
                        <span
                          key={chk}
                          className={`text-[10px] px-2 py-0.5 rounded-full border ${
                            pass
                              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                              : 'bg-red-950/40 border-red-800 text-red-300'
                          }`}
                        >
                          {chk}: {pass ? 'PASS' : 'FAIL'}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Event Timeline */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-[#a89485] uppercase tracking-wider">
                    Execution Trace Timeline ({selectedRunDetail.events?.length || 0} events)
                  </h4>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2 font-mono text-xs">
                    {(selectedRunDetail.events || []).map(ev => (
                      <div
                        key={ev.seq}
                        className="bg-[#1b120c] border border-[#352319] p-2.5 rounded-xl flex items-start gap-3"
                      >
                        <span className="text-[#6d5749] text-[10px] select-none pt-0.5">#{ev.seq}</span>
                        <div className="flex-1 space-y-0.5">
                          <div className="flex items-center justify-between">
                            <span className="text-[#f25c24] font-semibold text-[11px]">{ev.type}</span>
                            {ev.payload?.ms !== undefined && (
                              <span className="text-[#6d5749] text-[10px]">{ev.payload.ms}ms</span>
                            )}
                          </div>
                          <p className="text-[#c7bbb0] text-[11px] font-sans">
                            {ev.payload?.summary ||
                             ev.payload?.content ||
                             (ev.payload?.plan ? `Plan with ${ev.payload.plan.steps?.length} steps` : JSON.stringify(ev.payload))}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-[#22160f] border border-[#3b271d] rounded-2xl p-8 text-center text-xs text-[#8e7869]">
                Select a run to view its complete execution trace and event log.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Cpu,
  BookOpen,
  Brain,
  Workflow,
  ShieldCheck,
  Zap,
  TrendingUp,
  HardDrive,
  ThumbsUp,
  ThumbsDown,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Server,
  Activity,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { DashboardData, DashboardService } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const { setCurrentPage } = useApp();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    DashboardService.get()
      .then((res) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Failed to load telemetry');
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const totalRuns = data?.runs_per_day.reduce((acc, curr) => acc + curr.count, 0) || 0;
  const maxDayCount = Math.max(1, ...(data?.runs_per_day.map((d) => d.count) || [1]));

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-8 border-b border-[#302016] flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-[#f25c24]" />
            Dashboard
          </h1>
          <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
            Operational telemetry and local resource metrics computed via direct SQL aggregation.
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#241710] border border-[#3d291d] text-[11px] text-[#8e7869]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Local Engine Active</span>
        </div>
      </div>

      <div className="p-8 space-y-6 max-w-6xl">
        {/* Service Health Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-bold text-[#8e7869]">Ollama LLM</div>
              <div className="text-sm font-bold text-white mt-0.5">
                {data?.services_health.ollama ? 'Online (Qwen3)' : 'Unreachable'}
              </div>
            </div>
            {data?.services_health.ollama ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400" />
            )}
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-bold text-[#8e7869]">Database</div>
              <div className="text-sm font-bold text-white mt-0.5">
                {data?.services_health.db ? 'PostgreSQL 16' : 'Down'}
              </div>
            </div>
            {data?.services_health.db ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400" />
            )}
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-bold text-[#8e7869]">Vector Index</div>
              <div className="text-sm font-bold text-white mt-0.5">
                {data?.services_health.chroma ? 'Chroma HNSW' : 'Missing'}
              </div>
            </div>
            {data?.services_health.chroma ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400" />
            )}
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-4 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-bold text-[#8e7869]">Python Sandbox</div>
              <div className="text-sm font-bold text-white mt-0.5">
                {data?.services_health.sandbox ? 'Isolated' : 'Offline'}
              </div>
            </div>
            {data?.services_health.sandbox ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-5 h-5 text-amber-400" />
            )}
          </div>
        </div>

        {/* Metric Overview Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8e7869]">14-Day Runs</span>
              <Workflow className="w-4 h-4 text-[#f25c24]" />
            </div>
            <div className="text-2xl font-bold text-white">{totalRuns}</div>
            <p className="text-[11px] text-[#8e7869]">Total LangGraph workflows</p>
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8e7869]">Knowledge Base</span>
              <BookOpen className="w-4 h-4 text-[#d97706]" />
            </div>
            <div className="text-2xl font-bold text-white">{data?.files_count ?? 0} files</div>
            <p className="text-[11px] text-[#8e7869]">{data?.chunks_count ?? 0} indexed chunks</p>
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8e7869]">Confirmed Memories</span>
              <Brain className="w-4 h-4 text-[#3b82f6]" />
            </div>
            <div className="text-2xl font-bold text-white">{data?.memories_count ?? 0}</div>
            <p className="text-[11px] text-emerald-400">Strictly confirmed</p>
          </div>

          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#8e7869]">Satisfaction Ratio</span>
              <ThumbsUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              {Math.round((data?.feedback_ratio.ratio ?? 1.0) * 100)}%
            </div>
            <p className="text-[11px] text-[#8e7869]">
              +{data?.feedback_ratio.up ?? 0} / -{data?.feedback_ratio.down ?? 0} ratings
            </p>
          </div>
        </div>

        {/* 14-Day Activity Bar Chart (Lightweight SVG with CSS transform) */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-3xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#f25c24]" />
              <span>Workflow Runs per Day (Last 14 Days)</span>
            </h3>
            <span className="text-xs text-[#8e7869]">Tier distribution by day</span>
          </div>

          <div className="h-44 flex items-end gap-2 pt-6 pb-2 px-2 border-b border-[#302016]">
            {data?.runs_per_day.map((d, i) => {
              const heightPct = Math.max(6, (d.count / maxDayCount) * 100);
              const dayLabel = d.date.slice(5);
              return (
                <div key={d.date} className="flex-1 flex flex-col items-center gap-1.5 group relative">
                  {/* Tooltip */}
                  <div className="absolute -top-10 opacity-0 group-hover:opacity-100 transition-opacity bg-[#18110c] border border-[#3d291d] text-[10px] text-white px-2 py-1 rounded shadow-lg pointer-events-none z-10 whitespace-nowrap">
                    {d.date}: {d.count} runs (T1:{d.tier1}, T2:{d.tier2}, T3:{d.tier3})
                  </div>
                  {/* Bar */}
                  <div className="w-full bg-[#302016] rounded-t-sm overflow-hidden flex flex-col justify-end" style={{ height: '120px' }}>
                    <motion.div
                      initial={{ scaleY: 0 }}
                      animate={{ scaleY: 1 }}
                      transition={{ duration: 0.4, delay: i * 0.02 }}
                      style={{ originY: 1, height: `${heightPct}%` }}
                      className="w-full bg-gradient-to-t from-[#d97706] to-[#f25c24] rounded-t-sm"
                    />
                  </div>
                  <span className="text-[9px] text-[#8e7869] transform -rotate-45 origin-top-left mt-1">
                    {dayLabel}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Latency by Tier & Architecture */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#1b120c] p-5 rounded-2xl border border-[#302016] space-y-2">
            <div className="font-bold text-xs text-[#f25c24]">Tier 1: Simple Q&A</div>
            <div className="text-xl font-bold text-white">
              {data?.avg_latency_by_tier.tier1 ? `${data.avg_latency_by_tier.tier1} ms` : 'N/A'}
            </div>
            <p className="text-[11px] text-[#8e7869]">Reasoning only (1 LLM call)</p>
          </div>

          <div className="bg-[#1b120c] p-5 rounded-2xl border border-[#302016] space-y-2">
            <div className="font-bold text-xs text-[#d97706]">Tier 2: Document RAG</div>
            <div className="text-xl font-bold text-white">
              {data?.avg_latency_by_tier.tier2 ? `${data.avg_latency_by_tier.tier2} ms` : 'N/A'}
            </div>
            <p className="text-[11px] text-[#8e7869]">Hybrid search + Grounded reasoning</p>
          </div>

          <div className="bg-[#1b120c] p-5 rounded-2xl border border-[#302016] space-y-2">
            <div className="font-bold text-xs text-emerald-400">Tier 3: Complex Multi-Agent</div>
            <div className="text-xl font-bold text-white">
              {data?.avg_latency_by_tier.tier3 ? `${data.avg_latency_by_tier.tier3} ms` : 'N/A'}
            </div>
            <p className="text-[11px] text-[#8e7869]">Plan approval + Tools + Evaluation pass</p>
          </div>
        </div>

        {/* Recent Tasks linking to Workflows */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-3xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-[#f25c24]" />
              <span>Recent Workflow Executions</span>
            </h3>
            <button
              onClick={() => setCurrentPage('workflows')}
              className="text-xs text-[#f25c24] hover:text-[#d97706] font-medium flex items-center gap-1 transition-colors"
            >
              <span>View all workflows</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {data?.recent_tasks && data.recent_tasks.length > 0 ? (
            <div className="divide-y divide-[#302016]">
              {data.recent_tasks.map((task) => (
                <div key={task.run_id} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white truncate">{task.prompt}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-[#8e7869]">
                        {new Date(task.created_at).toLocaleTimeString()}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1b120c] border border-[#302016] text-[#a08c7e]">
                        Tier {task.tier}
                      </span>
                      {task.duration_ms && (
                        <span className="text-[10px] text-[#8e7869]">{task.duration_ms} ms</span>
                      )}
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      task.status === 'completed'
                        ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                        : task.status === 'running'
                        ? 'bg-amber-950/60 text-amber-400 border border-amber-800/40'
                        : 'bg-zinc-800 text-zinc-300'
                    }`}
                  >
                    {task.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-xs text-[#8e7869]">
              No workflow runs recorded yet. Start a chat to trigger execution.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

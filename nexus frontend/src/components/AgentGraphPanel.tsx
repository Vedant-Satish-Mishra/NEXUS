import React from 'react';
import { useApp } from '../context/AppContext';
import { GraphNodeId, GraphNodeStatus } from '../types';
import {
  Check,
  Pause,
  AlertCircle,
  Clock,
  FileText,
  RotateCcw,
  ExternalLink,
  ShieldCheck
} from 'lucide-react';

export const AgentGraphPanel: React.FC = () => {
  const {
    graphNodes,
    activeConversation,
    setPreviewDocument,
    documents,
    setCurrentPage
  } = useApp();

  const activeMsg = activeConversation?.messages.find(m => m.plan || m.citations);
  const plan = activeMsg?.plan;
  const isPaused = plan && plan.status === 'awaiting_approval';

  const getNodeClass = (status: GraphNodeStatus) => {
    switch (status) {
      case 'active':
        return 'bg-[#f25c24] text-white border-[#f8a581] shadow-lg shadow-[#f25c24]/30 animate-pulse';
      case 'waiting':
        return 'bg-[#2b1c13] text-[#f25c24] border-[#f25c24] shadow-md shadow-[#f25c24]/20 ring-2 ring-[#f25c24]/50';
      case 'done':
        return 'bg-[#2f1f16] text-[#e5dcd3] border-[#533929] hover:border-[#f25c24]/50';
      case 'skipped':
      case 'disabled':
        return 'bg-[#1e130c] text-[#5e4b3e] border-[#2e1d13] line-through opacity-60';
      default:
        return 'bg-[#22160f] text-[#8e7869] border-[#38251a]';
    }
  };

  const renderNode = (id: GraphNodeId, label: string, isSmall = false) => {
    const status = graphNodes[id];
    return (
      <div
        className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center justify-between gap-1.5 transition-all duration-200 ${
          isSmall ? 'w-28' : 'w-full max-w-[200px]'
        } ${getNodeClass(status)}`}
      >
        <span className="truncate">{label}</span>
        {status === 'done' && <Check className="w-3.5 h-3.5 text-emerald-400 stroke-[3]" />}
        {status === 'active' && <Clock className="w-3.5 h-3.5 text-white animate-spin" />}
        {status === 'waiting' && <span className="w-2 h-2 rounded-full bg-[#f25c24] animate-ping" />}
      </div>
    );
  };

  return (
    <aside className="w-80 bg-[#1b120c] border-l border-[#38261b] flex flex-col h-screen select-none shrink-0 text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-[#302016] flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white tracking-wide">Agent graph</h2>
          <p className="text-[11px] text-[#9c8779]">execution flowchart</p>
        </div>
        <div className="flex items-center gap-1.5 bg-[#251710] px-2.5 py-1 rounded-full border border-[#3b271d]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] text-[#f25c24] font-bold uppercase tracking-wider">
            live · tier 3
          </span>
        </div>
      </div>

      <div className="p-4 flex-1 space-y-6">
        {/* Graph Visual Pipeline */}
        <div className="relative flex flex-col items-center py-2 space-y-2">
          {/* Node 1: Understanding */}
          {renderNode('understanding', 'Understanding')}
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Node 2: Controller */}
          {renderNode('controller', 'Controller')}
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Parallel Nodes: Memory & Learning */}
          <div className="flex items-center justify-center gap-2 w-full max-w-[240px]">
            {renderNode('memory', 'Memory', true)}
            {renderNode('learning', 'Learning', true)}
          </div>
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Node 4: Planner (The central interactive node) */}
          <div className="relative">
            {renderNode('planner', 'Planner')}
            {/* Re-plan dashed arc simulation */}
            <div className="absolute -right-8 top-1/2 -translate-y-1/2 flex items-center">
              <span className="text-[9px] text-[#8e7869] italic transform rotate-90">re-plan</span>
            </div>
          </div>
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Parallel Nodes: Retrieval & Execute */}
          <div className="flex items-center justify-center gap-2 w-full max-w-[240px]">
            {renderNode('retrieval', 'Retrieval', true)}
            {renderNode('execute', 'Execute', true)}
          </div>
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Node 6: Reasoning */}
          {renderNode('reasoning', 'Reasoning')}
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Node 7: Evaluation */}
          {renderNode('evaluation', 'Evaluation')}
          <div className="w-0.5 h-2.5 bg-[#453023]" />

          {/* Node 8: Final Answer */}
          {renderNode('final_answer', 'Final answer')}
        </div>

        {/* State Notice Card */}
        {isPaused ? (
          <div className="bg-[#261810] border border-[#f25c24]/40 p-3.5 rounded-xl space-y-1.5 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
              <span className="text-xs font-bold text-amber-300">Run paused · plan saved</span>
            </div>
            <p className="text-[11px] text-[#a9978a] leading-relaxed">
              Resume anytime, even after a restart or page refresh. State is safely stored.
            </p>
          </div>
        ) : (
          <div className="bg-[#22160f] border border-[#3b271d] p-3 rounded-xl flex items-center gap-2 text-xs text-[#a9978a]">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>State persisted locally with LangGraph checkpoint.</span>
          </div>
        )}

        {/* Sources Section */}
        <div className="space-y-2 border-t border-[#302016] pt-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8e7869]">
              Sources
            </span>
            <button
              onClick={() => setCurrentPage('knowledge')}
              className="text-[11px] text-[#f25c24] hover:underline flex items-center gap-1 font-medium"
            >
              <span>Manage</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </button>
          </div>

          <div className="space-y-1.5">
            {activeMsg?.citations && activeMsg.citations.length > 0 ? (
              activeMsg.citations.map((c, i) => (
                <div
                  key={i}
                  onClick={() => {
                    const matchDoc = documents.find(d => d.name === c.filename || d.name.includes(c.filename.split('.')[0]));
                    if (matchDoc) {
                      setPreviewDocument(matchDoc);
                    }
                  }}
                  className="bg-[#241710] hover:bg-[#2e1d14] border border-[#3d291d] hover:border-[#f25c24]/50 p-2 rounded-lg cursor-pointer transition-colors group flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-[#f25c24] shrink-0" />
                    <span className="font-mono text-[11px] text-[#dfd6ce] truncate group-hover:text-white">
                      {c.filename} · p{c.page}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#8e7869] group-hover:text-[#f25c24]">View</span>
                </div>
              ))
            ) : (
              <div className="text-[11px] text-[#7d6758] italic py-1">
                No external document citations active.
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};

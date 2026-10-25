import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench, CheckCircle2, AlertCircle, Clock, Terminal } from 'lucide-react';

export interface ToolCardProps {
  tool: string;
  input: any;
  output?: any;
  status: 'proposed' | 'awaiting_approval' | 'running' | 'done' | 'error' | 'denied';
  durationMs?: number;
}

export const ToolCard: React.FC<ToolCardProps> = ({
  tool,
  input,
  output,
  status,
  durationMs,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'stdout' | 'raw'>('stdout');

  const statusColor = {
    proposed: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
    awaiting_approval: 'text-amber-300 bg-amber-950/60 border-amber-700 animate-pulse',
    running: 'text-blue-400 bg-blue-950/40 border-blue-800/40',
    done: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
    error: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
    denied: 'text-zinc-400 bg-zinc-900 border-zinc-700',
  }[status] || 'text-zinc-400 bg-zinc-900 border-zinc-700';

  const formatText = (val: any): string => {
    if (typeof val === 'string') return val;
    try {
      return JSON.stringify(val, null, 2);
    } catch {
      return String(val);
    }
  };

  return (
    <div className="my-2 bg-[#20140d] border border-[#3b271d] rounded-xl overflow-hidden text-xs">
      {/* Header Bar */}
      <div
        onClick={() => setExpanded(!expanded)}
        className="px-3.5 py-2.5 flex items-center justify-between cursor-pointer hover:bg-[#281911] transition-colors select-none"
      >
        <div className="flex items-center gap-2">
          {tool === 'python' ? (
            <Terminal className="w-4 h-4 text-amber-400" />
          ) : (
            <Wrench className="w-4 h-4 text-[#f25c24]" />
          )}
          <span className="font-semibold text-white uppercase tracking-wider text-[11px]">{tool}</span>
        </div>

        <div className="flex items-center gap-2">
          {durationMs !== undefined && durationMs > 0 && (
            <span className="text-[10px] text-[#8e7869] flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{durationMs}ms</span>
            </span>
          )}

          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border capitalize ${statusColor}`}>
            {status.replace('_', ' ')}
          </span>

          {expanded ? (
            <ChevronDown className="w-3.5 h-3.5 text-[#8e7869]" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 text-[#8e7869]" />
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="p-3.5 bg-[#170e09] border-t border-[#302016] space-y-3 font-mono">
          {/* Input */}
          <div className="space-y-1">
            <div className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#8e7869]">
              Input
            </div>
            <pre className="p-2.5 rounded-lg bg-[#120a06] border border-[#2a1a11] text-[11px] text-[#dfd6ce] overflow-x-auto whitespace-pre-wrap max-h-48">
              {formatText(input)}
            </pre>
          </div>

          {/* Output */}
          {output !== undefined && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#8e7869]">
                  Result
                </span>
                {typeof output === 'object' && output?.stdout !== undefined && (
                  <div className="flex gap-2 text-[10px] font-sans">
                    <button
                      onClick={() => setActiveTab('stdout')}
                      className={`${activeTab === 'stdout' ? 'text-[#f25c24] underline' : 'text-[#8e7869]'}`}
                    >
                      stdout
                    </button>
                    <button
                      onClick={() => setActiveTab('raw')}
                      className={`${activeTab === 'raw' ? 'text-[#f25c24] underline' : 'text-[#8e7869]'}`}
                    >
                      raw JSON
                    </button>
                  </div>
                )}
              </div>

              <pre className="p-2.5 rounded-lg bg-[#120a06] border border-[#2a1a11] text-[11px] text-emerald-300 overflow-x-auto whitespace-pre-wrap max-h-48">
                {activeTab === 'stdout' && typeof output === 'object' && output?.stdout !== undefined
                  ? output.stdout || (output.stderr ? `Error: ${output.stderr}` : '(empty output)')
                  : formatText(output)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

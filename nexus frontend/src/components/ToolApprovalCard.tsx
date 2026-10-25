import React, { useState } from 'react';
import { ToolCall } from '../types';
import { useApp } from '../context/AppContext';
import { Terminal, Play, X, Edit3, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface ToolApprovalCardProps {
  toolCall: ToolCall;
  messageId: string;
}

export const ToolApprovalCard: React.FC<ToolApprovalCardProps> = ({ toolCall, messageId }) => {
  const { approveTool, denyTool, runPythonCode } = useApp();
  const [isEditing, setIsEditing] = useState(false);
  const [code, setCode] = useState(toolCall.codeOrInput);
  const [isRunning, setIsRunning] = useState(false);
  const [executionOutput, setExecutionOutput] = useState<string | null>(toolCall.output || null);

  const handleRun = async () => {
    setIsRunning(true);
    const result = await runPythonCode(code);
    setIsRunning(false);
    setExecutionOutput(result);
    approveTool(messageId);
  };

  const handleDeny = () => {
    denyTool(messageId);
    setExecutionOutput('Execution denied by user.');
  };

  return (
    <div className="bg-[#241710] text-[#fbf8f2] border border-[#4a3426] rounded-2xl p-5 my-4 shadow-lg animate-fade-in space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#f25c24]/20 text-[#f25c24] flex items-center justify-center border border-[#f25c24]/30">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-bold text-sm text-white">Python sandbox</h4>
              <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 font-semibold px-2 py-0.5 rounded-full">
                Manual approval
              </span>
            </div>
            <p className="text-xs text-[#a9978a]">
              Isolated local container with strict resource limits and no network access.
            </p>
          </div>
        </div>
      </div>

      {/* Code Review block */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs text-[#9d897c]">
          <span className="font-medium">Review code before running:</span>
          {isEditing ? (
            <button
              onClick={() => setIsEditing(false)}
              className="text-emerald-400 hover:underline font-semibold"
            >
              Done editing
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="text-[#f25c24] hover:underline flex items-center gap-1 font-semibold"
            >
              <Edit3 className="w-3 h-3" />
              <span>Edit code</span>
            </button>
          )}
        </div>

        {isEditing ? (
          <textarea
            value={code}
            onChange={e => setCode(e.target.value)}
            rows={5}
            className="w-full bg-[#18100a] text-emerald-300 font-mono text-xs p-3 rounded-xl border border-[#4a3426] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
          />
        ) : (
          <div className="bg-[#18100a] rounded-xl border border-[#3b271d] p-3 font-mono text-xs overflow-x-auto text-[#dfd6ce]">
            {code.split('\n').map((line, idx) => (
              <div key={idx} className="flex gap-4">
                <span className="text-[#6d5749] select-none w-4 text-right">{idx + 1}</span>
                <span className="text-emerald-400 font-medium">{line}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Output Console (if run or denied) */}
      {executionOutput && (
        <div className="bg-[#140c07] rounded-xl border border-[#302016] p-3 text-xs font-mono space-y-1 text-[#c7bbb0]">
          <div className="text-[10px] uppercase font-bold text-[#8e7869] tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Output</span>
          </div>
          <pre className="whitespace-pre-wrap">{executionOutput}</pre>
        </div>
      )}

      {/* Actions */}
      {toolCall.status === 'awaiting_approval' && !executionOutput && (
        <div className="flex items-center gap-2 pt-2 border-t border-[#352319]">
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="bg-[#f25c24] hover:bg-[#d94c17] text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isRunning ? 'Running in sandbox...' : 'Run'}</span>
          </button>

          <button
            onClick={() => {
              setIsEditing(true);
            }}
            className="bg-[#2f1f16] hover:bg-[#3b271c] text-[#dfd6ce] text-xs font-semibold px-3 py-2 rounded-xl border border-[#4a3426] transition-colors"
          >
            Edit and run
          </button>

          <button
            onClick={handleDeny}
            className="bg-transparent hover:bg-red-950/30 text-red-400 text-xs font-semibold px-3 py-2 rounded-xl border border-red-900/40 hover:border-red-700 transition-colors flex items-center gap-1 ml-auto"
          >
            <X className="w-3.5 h-3.5" />
            <span>Deny</span>
          </button>
        </div>
      )}
    </div>
  );
};

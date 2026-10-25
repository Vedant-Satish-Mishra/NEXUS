import React from 'react';
import { AlertCircle, RefreshCw, Terminal, CheckCircle2 } from 'lucide-react';

export interface OllamaHelpCardProps {
  onRetry: () => void;
  isRetrying?: boolean;
}

export const OllamaHelpCard: React.FC<OllamaHelpCardProps> = ({ onRetry, isRetrying = false }) => {
  return (
    <div className="bg-[#241710] border border-amber-900/60 rounded-2xl p-5 space-y-4 max-w-xl mx-auto my-4 text-xs">
      <div className="flex items-center gap-2.5 text-amber-400">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <h3 className="font-bold text-sm text-white">Local Ollama LLM Unreachable</h3>
      </div>

      <p className="text-[#a08c7e] leading-relaxed">
        NEXUS runs models locally via Ollama on your Windows host. Ensure the Ollama server process is running:
      </p>

      <div className="space-y-2 bg-[#170e09] border border-[#302016] p-3 rounded-xl font-mono text-[11px] text-[#dfd6ce]">
        <div className="flex items-center gap-2 text-[#8e7869]">
          <Terminal className="w-3.5 h-3.5" />
          <span>1. Open PowerShell or Command Prompt</span>
        </div>
        <div className="text-amber-300 font-semibold pl-5">ollama serve</div>
        <div className="flex items-center gap-2 text-[#8e7869] pt-1">
          <Terminal className="w-3.5 h-3.5" />
          <span>2. Ensure the Qwen3 model is pulled</span>
        </div>
        <div className="text-amber-300 font-semibold pl-5">ollama pull qwen3:4b</div>
      </div>

      <div className="flex justify-end pt-1">
        <button
          onClick={onRetry}
          disabled={isRetrying}
          className="bg-[#f25c24] hover:bg-[#d97706] disabled:opacity-50 text-white font-semibold px-4 py-2 rounded-xl flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
          <span>Retry Connection</span>
        </button>
      </div>
    </div>
  );
};

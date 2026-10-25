import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { AgentConfig, AgentPreset, ModelProfile } from '../types';
import {
  X,
  Zap,
  BarChart3,
  Check,
  Sparkles,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export const NewChatModal: React.FC = () => {
  const {
    isNewChatModalOpen,
    setIsNewChatModalOpen,
    createNewConversation
  } = useApp();

  const [preset, setPreset] = useState<AgentPreset>('balanced');
  const [model, setModel] = useState<ModelProfile>('fast');
  const [askBeforePlan, setAskBeforePlan] = useState<boolean>(true);
  const [initialPrompt, setInitialPrompt] = useState<string>('');

  const [config, setConfig] = useState<AgentConfig>({
    controller: true,
    planner: true,
    retrieval: true,
    reasoning: true,
    memory: true,
    learning: true,
    evaluation: true
  });

  if (!isNewChatModalOpen) return null;

  const handlePresetChange = (newPreset: AgentPreset) => {
    setPreset(newPreset);
    if (newPreset === 'fast') {
      setConfig({
        controller: true,
        planner: false,
        retrieval: false,
        reasoning: true,
        memory: false,
        learning: false,
        evaluation: false
      });
    } else if (newPreset === 'balanced') {
      setConfig({
        controller: true,
        planner: false,
        retrieval: true,
        reasoning: true,
        memory: true,
        learning: false,
        evaluation: true
      });
    } else {
      setConfig({
        controller: true,
        planner: true,
        retrieval: true,
        reasoning: true,
        memory: true,
        learning: true,
        evaluation: true
      });
    }
  };

  const handleStartChat = () => {
    createNewConversation(preset, config, model, askBeforePlan, initialPrompt);
    setInitialPrompt('');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl relative animate-fade-in my-8">
        {/* Close Button */}
        <button
          onClick={() => setIsNewChatModalOpen(false)}
          className="absolute top-5 right-5 p-2 rounded-full hover:bg-[#ede3d3] text-[#786558] hover:text-[#1e140f] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Brand Lockup */}
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-lg bg-[#f25c24] flex items-center justify-center p-1">
            <img src="/nexus_logo.png" alt="NEXUS" className="w-full h-full object-contain filter invert" />
          </div>
          <span className="font-serif-brand font-bold text-lg tracking-wider text-[#1e140f]">NEXUS</span>
        </div>

        {/* Title & Description */}
        <h2 className="text-2xl font-bold text-[#1e140f] tracking-tight">
          Start a new chat
        </h2>
        <p className="text-xs text-[#786558] italic mt-1 leading-relaxed">
          Configure your agents and settings. Choose the right balance for your task, then start a conversation.
        </p>

        <div className="space-y-6 mt-6">
          {/* Agent preset selector */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#1e140f] uppercase tracking-wide block">
              Agent preset
            </label>
            <p className="text-[11px] text-[#786558]">Pre-configured agents for different needs.</p>

            <div className="grid grid-cols-3 gap-2 bg-[#f0e8dc] p-1.5 rounded-2xl border border-[#d8cbb8]">
              {(['fast', 'balanced', 'full'] as AgentPreset[]).map(p => {
                const isSelected = preset === p;
                return (
                  <button
                    key={p}
                    onClick={() => handlePresetChange(p)}
                    className={`py-2 rounded-xl text-xs font-semibold capitalize transition-all ${
                      isSelected
                        ? 'bg-[#f25c24] text-white shadow-md shadow-[#f25c24]/20'
                        : 'text-[#5f4e42] hover:bg-[#e4d8c8]'
                    }`}
                  >
                    {p}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Left: Agent Configuration Toggles */}
            <div className="space-y-2.5 bg-[#f7f2ea] p-4 rounded-2xl border border-[#e4d9c7]">
              <label className="text-xs font-bold text-[#1e140f] uppercase tracking-wide block">
                Agent configuration
              </label>
              <p className="text-[11px] text-[#786558]">Choose which agents to use in this chat.</p>

              <div className="space-y-2 pt-1 text-xs">
                {/* Controller (always on) */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Controller <span className="text-[10px] text-[#8e7869] italic">(always on)</span></span>
                  <div className="w-8 h-4.5 rounded-full bg-[#f25c24] p-0.5 flex items-center justify-end">
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </div>
                </div>

                {/* Planner */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Planner</span>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, planner: !prev.planner }))}
                    className={`w-8 h-4.5 rounded-full p-0.5 flex items-center transition-colors ${
                      config.planner ? 'bg-[#f25c24] justify-end' : 'bg-[#d8cbb8] justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </button>
                </div>

                {/* Retrieval */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Retrieval</span>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, retrieval: !prev.retrieval }))}
                    className={`w-8 h-4.5 rounded-full p-0.5 flex items-center transition-colors ${
                      config.retrieval ? 'bg-[#f25c24] justify-end' : 'bg-[#d8cbb8] justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </button>
                </div>

                {/* Reasoning (always on) */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Reasoning <span className="text-[10px] text-[#8e7869] italic">(always on)</span></span>
                  <div className="w-8 h-4.5 rounded-full bg-[#f25c24] p-0.5 flex items-center justify-end">
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </div>
                </div>

                {/* Memory */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Memory</span>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, memory: !prev.memory }))}
                    className={`w-8 h-4.5 rounded-full p-0.5 flex items-center transition-colors ${
                      config.memory ? 'bg-[#f25c24] justify-end' : 'bg-[#d8cbb8] justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </button>
                </div>

                {/* Learning */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Learning</span>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, learning: !prev.learning }))}
                    className={`w-8 h-4.5 rounded-full p-0.5 flex items-center transition-colors ${
                      config.learning ? 'bg-[#f25c24] justify-end' : 'bg-[#d8cbb8] justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </button>
                </div>

                {/* Evaluation */}
                <div className="flex items-center justify-between">
                  <span className="font-medium text-[#1e140f]">Evaluation</span>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, evaluation: !prev.evaluation }))}
                    className={`w-8 h-4.5 rounded-full p-0.5 flex items-center transition-colors ${
                      config.evaluation ? 'bg-[#f25c24] justify-end' : 'bg-[#d8cbb8] justify-start'
                    }`}
                  >
                    <div className="w-3.5 h-3.5 rounded-full bg-white shadow" />
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Local Model Profile & Plan Execution Preference */}
            <div className="space-y-4">
              {/* Local model profile */}
              <div className="space-y-2 bg-[#f7f2ea] p-4 rounded-2xl border border-[#e4d9c7]">
                <label className="text-xs font-bold text-[#1e140f] uppercase tracking-wide block">
                  Local model profile
                </label>
                <p className="text-[11px] text-[#786558]">Optimise speed or quality for this chat.</p>

                <div className="space-y-2 pt-1">
                  {/* Fast */}
                  <div
                    onClick={() => setModel('fast')}
                    className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                      model === 'fast'
                        ? 'border-[#f25c24] bg-white ring-1 ring-[#f25c24]'
                        : 'border-[#d8cbb8] bg-[#fbf8f2] hover:border-[#bfaaa0]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Zap className="w-4 h-4 text-[#f25c24]" />
                      <div>
                        <div className="font-bold text-xs text-[#1e140f]">Fast</div>
                        <div className="text-[10px] text-[#786558]">Faster responses (Qwen3 4B)</div>
                      </div>
                    </div>
                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                      model === 'fast' ? 'border-[#f25c24] bg-[#f25c24]' : 'border-[#bfaaa0]'
                    }`}>
                      {model === 'fast' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </div>
                  </div>

                  {/* Quality */}
                  <div
                    onClick={() => setModel('quality')}
                    className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                      model === 'quality'
                        ? 'border-[#f25c24] bg-white ring-1 ring-[#f25c24]'
                        : 'border-[#d8cbb8] bg-[#fbf8f2] hover:border-[#bfaaa0]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <BarChart3 className="w-4 h-4 text-[#d97706]" />
                      <div>
                        <div className="font-bold text-xs text-[#1e140f]">Quality</div>
                        <div className="text-[10px] text-[#786558]">Higher quality reasoning (Qwen3 8B)</div>
                      </div>
                    </div>
                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                      model === 'quality' ? 'border-[#f25c24] bg-[#f25c24]' : 'border-[#bfaaa0]'
                    }`}>
                      {model === 'quality' && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </div>
                  </div>
                </div>
              </div>

              {/* Plan execution option */}
              <div className="bg-[#f7f2ea] p-4 rounded-2xl border border-[#e4d9c7] space-y-1.5">
                <label className="text-xs font-bold text-[#1e140f] uppercase tracking-wide block">
                  Plan execution
                </label>
                <p className="text-[11px] text-[#786558]">Control when the plan runs.</p>
                <label className="flex items-center gap-2 cursor-pointer pt-1 text-xs font-medium text-[#1e140f]">
                  <input
                    type="checkbox"
                    checked={askBeforePlan}
                    onChange={e => setAskBeforePlan(e.target.checked)}
                    className="w-4 h-4 rounded text-[#f25c24] focus:ring-[#f25c24] accent-[#f25c24]"
                  />
                  <span>Ask before plan execution</span>
                </label>
              </div>
            </div>
          </div>

          {/* Optional Prompt Field */}
          <div>
            <input
              type="text"
              placeholder="What would you like NEXUS to do? (optional)"
              value={initialPrompt}
              onChange={e => setInitialPrompt(e.target.value)}
              className="w-full text-xs p-3 rounded-xl border border-[#d8cbb8] bg-white text-[#1e140f] focus:outline-none focus:ring-2 focus:ring-[#f25c24]"
            />
          </div>

          {/* Action button */}
          <button
            onClick={handleStartChat}
            className="w-full bg-[#f25c24] hover:bg-[#d94c17] text-white font-bold py-3.5 px-6 rounded-2xl shadow-lg shadow-[#f25c24]/20 flex items-center justify-center gap-2 text-sm transition-all hover:scale-[1.01] active:scale-100"
          >
            <span>Start chat</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

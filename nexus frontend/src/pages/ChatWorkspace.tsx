import React, { useState, useRef, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { UnderstandingCard } from '../components/UnderstandingCard';
import { PlanApprovalCard } from '../components/PlanApprovalCard';
import { ToolApprovalCard } from '../components/ToolApprovalCard';
import { MemoryProposalCard } from '../components/MemoryProposalCard';
import { FeedbackButtons } from '../components/FeedbackButtons';
import {
  Send,
  Paperclip,
  Mic,
  Star,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  FileText,
  User,
  Sparkles,
  ShieldCheck,
  Terminal
} from 'lucide-react';

export const ChatWorkspace: React.FC = () => {
  const {
    activeConversation,
    sendMessage,
    isProcessing,
    setPreviewDocument,
    documents
  } = useApp();

  const [inputPrompt, setInputPrompt] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [voiceActive, setVoiceActive] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConversation?.messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || isProcessing) return;
    sendMessage(inputPrompt);
    setInputPrompt('');
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleVoice = () => {
    setVoiceActive(!voiceActive);
    if (!voiceActive) {
      setInputPrompt('Create an updated 4-month preparation plan focusing on Java and DSA.');
    }
  };

  if (!activeConversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#18110c] text-[#a08c7e]">
        <div className="text-center space-y-2">
          <p className="text-sm">No active conversation.</p>
          <p className="text-xs text-[#705c50]">Choose or start a chat from the sidebar.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-hidden">
      {/* Chat Top Header */}
      <header className="px-6 py-4 border-b border-[#302016] flex items-center justify-between bg-[#1b120c]/90 backdrop-blur-sm z-10 shrink-0">
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">
            {activeConversation.title}
          </h1>
          <div className="flex items-center gap-2 mt-0.5 text-xs text-[#9d897c]">
            <span className="capitalize">{activeConversation.agentPreset} preset</span>
            <span>·</span>
            <span className="capitalize">{activeConversation.modelProfile} model profile</span>
            <span>·</span>
            <span>Local privacy guaranteed</span>
          </div>
        </div>

        {/* 5-dot rating / status */}
        <div className="flex items-center gap-1.5" title="Satisfaction rating">
          {[1, 2, 3, 4, 5].map(star => (
            <span
              key={star}
              className="w-2 h-2 rounded-full bg-[#f25c24] opacity-80"
            />
          ))}
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-6">
        {activeConversation.messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 text-[#8e7869] space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-[#2b1c13] flex items-center justify-center text-[#f25c24] border border-[#3d291d]">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">How can NEXUS assist your studies today?</h3>
            <p className="text-xs max-w-md leading-relaxed text-[#a08c7e]">
              Ask a question, upload research notes, or request a complex study roadmap. All reasoning and retrieval runs locally on your machine.
            </p>
          </div>
        ) : (
          activeConversation.messages.map(msg => {
            const isUser = msg.role === 'user';

            return (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-4xl mx-auto ${
                  isUser ? 'justify-end' : 'justify-start'
                } animate-fade-in`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-[#f25c24] flex items-center justify-center shrink-0 p-1 mt-1 shadow-sm shadow-[#f25c24]/20">
                    <img src="/nexus_logo.png" alt="NEXUS" className="w-full h-full object-contain filter invert" />
                  </div>
                )}

                <div className={`space-y-3 max-w-2xl ${isUser ? 'w-auto' : 'w-full'}`}>
                  {/* User Bubble */}
                  {isUser ? (
                    <div className="bg-[#f25c24] text-white font-medium p-4 rounded-3xl rounded-tr-md shadow-md shadow-[#f25c24]/10 text-sm leading-relaxed">
                      {msg.content}
                    </div>
                  ) : (
                    /* Assistant Message Body */
                    <div className="space-y-3">
                      {/* Understanding Card */}
                      {msg.understanding && (
                        <UnderstandingCard understanding={msg.understanding} />
                      )}

                      {/* Plan Approval Card */}
                      {msg.plan && (
                        <PlanApprovalCard plan={msg.plan} messageId={msg.id} />
                      )}

                      {/* Tool Approval Card */}
                      {msg.toolCall && (
                        <ToolApprovalCard toolCall={msg.toolCall} messageId={msg.id} />
                      )}

                      {/* Main Message Content */}
                      {msg.content && (
                        <div className="bg-[#241710] border border-[#3b271d] text-[#e8ded6] p-5 rounded-3xl text-sm leading-relaxed shadow-sm space-y-2">
                          <div className="whitespace-pre-wrap">{msg.content}</div>

                          {/* Action footer */}
                          <div className="flex items-center justify-between pt-3 border-t border-[#342217] text-xs text-[#8e7869]">
                            <span className="text-[11px] font-mono">{msg.timestamp}</span>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleCopy(msg.id, msg.content)}
                                className="hover:text-white p-1 rounded transition-colors"
                                title="Copy response"
                              >
                                {copiedId === msg.id ? (
                                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <Copy className="w-3.5 h-3.5" />
                                )}
                              </button>
                              <FeedbackButtons messageId={msg.id} />
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Memory Proposals */}
                      {msg.memoriesProposed && msg.memoriesProposed.length > 0 && (
                        <div className="space-y-1">
                          {msg.memoriesProposed.map(mem => (
                            <MemoryProposalCard key={mem.id} memory={mem} />
                          ))}
                        </div>
                      )}

                      {/* Evaluation Badge (Tier 3 verification) */}
                      {msg.evaluation && (
                        <div className="bg-[#1c120a] border border-emerald-900/40 p-2.5 rounded-xl text-xs flex items-center justify-between text-emerald-300">
                          <div className="flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                            <span className="font-semibold">Evaluation Verified ({Math.round(msg.evaluation.score * 100)}%)</span>
                            <span className="text-[11px] text-[#a9978a]">— {msg.evaluation.feedback}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-[#2e1f16] border border-[#483325] flex items-center justify-center shrink-0 mt-1 text-[#dfd6ce]">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Composer Bottom Area */}
      <div className="p-4 sm:p-6 bg-[#18110c] border-t border-[#302016] shrink-0">
        <form
          onSubmit={handleSend}
          className="max-w-4xl mx-auto relative bg-[#241710] border border-[#3d291d] focus-within:border-[#f25c24] rounded-2xl p-2 transition-colors flex items-center gap-2 shadow-lg"
        >
          {/* File Attachment */}
          <button
            type="button"
            className="p-2 rounded-xl text-[#8e7869] hover:text-[#fbf8f2] hover:bg-[#2f1f16] transition-colors"
            title="Attach document to conversation"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Voice input */}
          <button
            type="button"
            onClick={toggleVoice}
            className={`p-2 rounded-xl transition-colors ${
              voiceActive ? 'text-[#f25c24] bg-[#f25c24]/20 animate-pulse' : 'text-[#8e7869] hover:text-[#fbf8f2] hover:bg-[#2f1f16]'
            }`}
            title="Voice input"
          >
            <Mic className="w-4 h-4" />
          </button>

          {/* Input Textarea */}
          <input
            type="text"
            value={inputPrompt}
            onChange={e => setInputPrompt(e.target.value)}
            disabled={isProcessing}
            placeholder={isProcessing ? 'Executive Controller is coordinating agents...' : 'Ask NEXUS anything...'}
            className="flex-1 bg-transparent text-sm text-[#fbf8f2] placeholder-[#8e7869] focus:outline-none px-2"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputPrompt.trim() || isProcessing}
            className="w-9 h-9 rounded-xl bg-[#f25c24] hover:bg-[#d94c17] disabled:opacity-40 disabled:hover:bg-[#f25c24] text-white flex items-center justify-center transition-all shrink-0 shadow-md shadow-[#f25c24]/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="text-[10px] text-center text-[#786558] mt-2">
          Local Qwen3 inference · ChromaDB vectors · 100% private to this laptop
        </p>
      </div>
    </div>
  );
};

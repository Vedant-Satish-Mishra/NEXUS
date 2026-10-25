import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { MemoryItem } from '../types';
import {
  Brain,
  Search,
  Check,
  X,
  Edit3,
  Trash2,
  Bookmark,
  Target,
  Settings2,
  BookOpen,
  Plus,
  AlertTriangle,
  ShieldCheck
} from 'lucide-react';

export const MemoryPage: React.FC = () => {
  const {
    memories,
    saveMemory,
    dismissMemory,
    deleteMemory,
    deleteAllMemories,
    addMemoryManually
  } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterTab, setFilterTab] = useState<'all' | 'saved' | 'pending'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfirmDeleteAll, setShowConfirmDeleteAll] = useState(false);

  const [newContent, setNewContent] = useState('');
  const [newImportance, setNewImportance] = useState<'high' | 'medium' | 'low'>('medium');

  const pendingMemories = memories.filter(m => m.status === 'pending');
  const savedMemories = memories.filter(m => m.status === 'saved');

  const filteredMemories = memories.filter(m => {
    const matchesSearch = m.content.toLowerCase().includes(searchQuery.toLowerCase());
    if (filterTab === 'saved') return matchesSearch && m.status === 'saved';
    if (filterTab === 'pending') return matchesSearch && m.status === 'pending';
    return matchesSearch;
  });

  const getImportanceBadge = (importance: string) => {
    switch (importance) {
      case 'high':
        return 'bg-red-500/20 text-red-300 border-red-500/30';
      case 'medium':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'goal':
        return <BookOpen className="w-4 h-4 text-[#f25c24]" />;
      case 'preference':
        return <Settings2 className="w-4 h-4 text-[#d97706]" />;
      default:
        return <Target className="w-4 h-4 text-[#3b82f6]" />;
    }
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newContent.trim()) {
      addMemoryManually(newContent, newImportance);
      setNewContent('');
      setShowAddModal(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-8 border-b border-[#302016] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Memory</h1>
            <span className="text-xs bg-[#f25c24]/20 text-[#f25c24] border border-[#f25c24]/30 font-semibold px-2.5 py-0.5 rounded-full">
              Consent-First
            </span>
          </div>
          <h2 className="text-base font-bold text-[#d97706] mt-1 font-serif-brand tracking-wide">
            Only confirmed memories are saved
          </h2>
          <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
            NEXUS remembers your preferences, goals and context to personalise responses. You stay in control.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="bg-[#f25c24] hover:bg-[#d94c17] text-white font-semibold text-xs px-5 py-3 rounded-xl shadow-lg shadow-[#f25c24]/20 flex items-center justify-center gap-2 self-start sm:self-auto transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add memory</span>
        </button>
      </div>

      <div className="p-8 space-y-6 max-w-5xl">
        {/* Search & Tabs */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-[#241710] border border-[#3d291d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-1.5 bg-[#241710] p-1 rounded-xl border border-[#3d291d] shrink-0">
            {(['all', 'saved', 'pending'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setFilterTab(tab)}
                className={`text-xs px-4 py-1.5 rounded-lg font-medium capitalize transition-colors ${
                  filterTab === tab
                    ? 'bg-[#f25c24] text-white'
                    : 'text-[#8e7869] hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* PENDING MEMORY PROPOSALS SECTION */}
        {(filterTab === 'all' || filterTab === 'pending') && pendingMemories.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#d97706]">
                  Pending memory proposals
                </span>
                <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                  <span>Needs your confirmation</span>
                </span>
              </div>
            </div>

            <div className="space-y-2.5">
              {pendingMemories.map(m => (
                <div
                  key={m.id}
                  className="bg-[#241710] border border-[#f25c24]/40 rounded-2xl p-4 shadow-sm space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium text-white">{m.content}</p>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border capitalize shrink-0 ${getImportanceBadge(
                        m.importance
                      )}`}
                    >
                      {m.importance}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#8e7869]">{m.sourceChat}</div>

                  <div className="flex items-center gap-2 pt-2 border-t border-[#342217]">
                    <button
                      onClick={() => saveMemory(m.id)}
                      className="bg-[#f25c24] hover:bg-[#d94c17] text-white text-xs font-semibold px-4 py-1.5 rounded-lg transition-colors flex items-center gap-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={() => dismissMemory(m.id)}
                      className="text-xs text-[#8e7869] hover:text-white px-3 py-1.5 rounded-lg"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SAVED MEMORIES SECTION */}
        {(filterTab === 'all' || filterTab === 'saved') && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#a08c7e]">
                Saved memories ({savedMemories.length})
              </span>
            </div>

            <div className="space-y-2.5">
              {savedMemories.length === 0 ? (
                <div className="bg-[#22160f] border border-[#3b271d] rounded-2xl p-8 text-center text-xs text-[#8e7869]">
                  No confirmed memories yet. NEXUS only remembers preferences after you approve them.
                </div>
              ) : (
                savedMemories.map(m => (
                  <div
                    key={m.id}
                    className="bg-[#22160f] border border-[#3b271d] hover:border-[#4d3323] rounded-2xl p-4 flex items-center justify-between gap-4 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-xl bg-[#2d1d14] flex items-center justify-center shrink-0">
                        {getCategoryIcon(m.category)}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white leading-snug">
                          {m.content}
                        </div>
                        <div className="text-[11px] text-[#8e7869] mt-0.5">
                          Source: {m.sourceChat} · {m.date}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border capitalize ${getImportanceBadge(
                          m.importance
                        )}`}
                      >
                        {m.importance}
                      </span>
                      <button
                        onClick={() => deleteMemory(m.id)}
                        className="opacity-0 group-hover:opacity-100 text-[#8e7869] hover:text-red-400 p-1 transition-opacity"
                        title="Delete memory"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Danger Zone: Delete All Memories */}
        {savedMemories.length > 0 && (
          <div className="pt-6 border-t border-[#302016] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <button
              onClick={() => setShowConfirmDeleteAll(true)}
              className="border border-red-900/50 hover:bg-red-950/20 text-red-400 font-semibold text-xs py-2.5 px-4 rounded-xl flex items-center gap-2 self-start transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete all memories</span>
            </button>
            <p className="text-[11px] text-[#786558] max-w-sm">
              This will permanently remove all saved memories from PostgreSQL and vectors from ChromaDB.
            </p>
          </div>
        )}

        {/* Add Memory Modal */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl p-6 max-w-md w-full shadow-2xl animate-fade-in relative">
              <button
                onClick={() => setShowAddModal(false)}
                className="absolute top-5 right-5 p-1.5 rounded-full hover:bg-[#ede3d3] text-[#786558]"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="text-xl font-bold text-[#1e140f]">Add a confirmed memory</h3>
              <p className="text-xs text-[#786558] mt-1 mb-4">
                Explicitly store a stable goal, preference, or technical context for your chats.
              </p>

              <form onSubmit={handleAddSubmit} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#1e140f] block mb-1">
                    Memory Content
                  </label>
                  <textarea
                    rows={3}
                    required
                    placeholder="e.g. Always write Java code examples following Google Java Style Guide."
                    value={newContent}
                    onChange={e => setNewContent(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-[#cbb8a3] bg-white text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1e140f] block mb-1">
                    Importance Level
                  </label>
                  <select
                    value={newImportance}
                    onChange={e => setNewImportance(e.target.value as any)}
                    className="w-full text-xs p-2.5 rounded-xl border border-[#cbb8a3] bg-white text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                  >
                    <option value="high">High (Recalled in most reasoning prompts)</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-[#786558]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2.5 text-xs font-bold bg-[#f25c24] text-white rounded-xl hover:bg-[#d94c17]"
                  >
                    Save memory
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Confirm Delete All Modal */}
        {showConfirmDeleteAll && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#241710] text-white border border-[#4a3426] rounded-3xl p-6 max-w-sm w-full shadow-2xl animate-fade-in space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mx-auto">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Permanently erase all memories?</h3>
              <p className="text-xs text-[#a08c7e] leading-relaxed">
                This action is irreversible and purges all confirmed memory vectors from ChromaDB and records from PostgreSQL.
              </p>
              <div className="flex items-center justify-center gap-3 pt-2">
                <button
                  onClick={() => setShowConfirmDeleteAll(false)}
                  className="px-4 py-2 text-xs font-semibold bg-[#352319] hover:bg-[#432d20] rounded-xl text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    deleteAllMemories();
                    setShowConfirmDeleteAll(false);
                  }}
                  className="px-4 py-2 text-xs font-bold bg-red-600 hover:bg-red-700 text-white rounded-xl"
                >
                  Yes, erase all
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

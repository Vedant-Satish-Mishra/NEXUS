import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useApp } from '../context/AppContext';
import { AgentPreset, AgentType, AppPage } from '../types';
import { spring } from '../lib/motion';
import {
  MessageSquare,
  BookOpen,
  Brain,
  Workflow,
  Wrench,
  Settings,
  LayoutDashboard,
  Plus,
  Trash2,
  Lock,
  Radio,
  Sliders,
  CheckCircle2,
  Sparkles
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const {
    currentPage,
    setCurrentPage,
    conversations,
    activeConversationId,
    setActiveConversationId,
    deleteConversation,
    setIsNewChatModalOpen,
    activeConversation
  } = useApp();

  const presets: AgentPreset[] = ['fast', 'balanced', 'full'];

  const agentList: { type: AgentType; name: string; locked?: boolean }[] = [
    { type: 'controller', name: 'Controller', locked: true },
    { type: 'planner', name: 'Planner' },
    { type: 'retrieval', name: 'Retrieval' },
    { type: 'reasoning', name: 'Reasoning', locked: true },
    { type: 'memory', name: 'Memory' },
    { type: 'learning', name: 'Learning' },
    { type: 'evaluation', name: 'Evaluation' }
  ];

  return (
    <aside className="w-72 bg-[#1b120c] border-r border-[#38261b] flex flex-col h-screen select-none shrink-0 text-[#fbf8f2]">
      {/* Brand Header */}
      <div className="p-4 flex items-center justify-between border-b border-[#302016]">
        <div 
          onClick={() => setCurrentPage('chat')} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-[#f25c24] flex items-center justify-center p-1 shadow-md shadow-[#f25c24]/20 group-hover:scale-105 transition-transform">
            <img src="/nexus_logo.png" alt="NEXUS logo" className="w-full h-full object-contain filter invert" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-serif-brand text-2xl font-bold tracking-wider text-[#ffffff]">NEXUS</span>
              <span className="text-[10px] bg-[#f25c24]/20 text-[#f25c24] px-1.5 py-0.5 rounded font-mono font-medium">v1.0</span>
            </div>
            <p className="text-[11px] text-[#a08c7e] tracking-tight -mt-0.5">cognitive system</p>
          </div>
        </div>
      </div>

      {/* Main Action: + New Chat */}
      <div className="p-4 pb-2">
        <button
          onClick={() => setIsNewChatModalOpen(true)}
          className="w-full bg-[#f25c24] hover:bg-[#d94c17] text-white font-medium py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-[#f25c24]/20 transition-all hover:-translate-y-0.5 active:translate-y-0"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>New chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
        {/* AGENTS CONFIGURATION SECTION */}
        <div className="space-y-2">
          <div className="flex items-center justify-between px-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#8e7869]">Agents</span>
            <span className="text-[10px] text-[#f25c24] font-medium capitalize">
              {activeConversation?.agentPreset || 'Balanced'}
            </span>
          </div>

          {/* Preset Buttons */}
          <div className="grid grid-cols-3 gap-1 bg-[#241710] p-1 rounded-lg border border-[#3d291d]">
            {presets.map(p => {
              const isActive = activeConversation?.agentPreset === p;
              return (
                <button
                  key={p}
                  disabled
                  className={`text-xs py-1 rounded capitalize font-medium transition-colors ${
                    isActive
                      ? 'bg-[#f25c24] text-white shadow-sm'
                      : 'text-[#9c8779] hover:text-[#fbf8f2]'
                  }`}
                >
                  {p}
                </button>
              );
            })}
          </div>

          {/* Individual Agent Toggles */}
          <div className="space-y-1.5 pt-1 px-1">
            {agentList.map(a => {
              const isEnabled = activeConversation ? activeConversation.agentConfig[a.type] : true;
              return (
                <div
                  key={a.type}
                  className="flex items-center justify-between text-xs py-1 px-1.5 rounded hover:bg-[#261811] transition-colors"
                >
                  <span className={`font-medium ${isEnabled ? 'text-[#e8ded6]' : 'text-[#6f5b4e]'}`}>
                    {a.name}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {a.locked && (
                      <span className="text-[10px] text-[#7d6758] italic font-normal">always on</span>
                    )}
                    <div
                      className={`w-7 h-4 rounded-full p-0.5 flex items-center transition-colors ${
                        isEnabled ? 'bg-[#f25c24]' : 'bg-[#3b271d]'
                      }`}
                    >
                      <div
                        className={`w-3 h-3 rounded-full bg-white transition-transform ${
                          isEnabled ? 'translate-x-3' : 'translate-x-0'
                        }`}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* RECENT CHATS */}
        <div className="space-y-1">
          <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wider text-[#8e7869]">
            Chats
          </div>
          <div className="space-y-1">
            {conversations.map(conv => {
              const isActive = currentPage === 'chat' && conv.id === activeConversationId;
              return (
                <div
                  key={conv.id}
                  onClick={() => {
                    setActiveConversationId(conv.id);
                    setCurrentPage('chat');
                  }}
                  className={`group relative flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-all ${
                    isActive
                      ? 'bg-[#2b1c13] text-[#ffffff] border border-[#f25c24]/40 shadow-sm'
                      : 'text-[#b8a495] hover:bg-[#241710] hover:text-[#fbf8f2]'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#f25c24]' : 'text-[#856f60]'}`} />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  {conversations.length > 1 && (
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-[#856f60] hover:text-red-400 p-1 transition-opacity"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* NAVIGATION LINKS */}
        <div className="space-y-1 border-t border-[#302016] pt-3">
          <div className="px-2 pb-1 text-[11px] font-bold uppercase tracking-wider text-[#8e7869]">
            Workspace
          </div>
          {[
            { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, color: 'text-[#f59e0b]' },
            { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen, color: 'text-[#f25c24]' },
            { id: 'memory', label: 'Memory', icon: Brain, color: 'text-[#d97706]' },
            { id: 'workflows', label: 'Workflows', icon: Workflow, color: 'text-[#2563eb]' },
            { id: 'tools', label: 'Tools & Sandbox', icon: Wrench, color: 'text-[#16a34a]' },
            { id: 'settings', label: 'Settings', icon: Settings, color: 'text-[#9ca3af]' },
          ].map((nav) => {
            const isActive = currentPage === nav.id;
            const Icon = nav.icon;
            return (
              <button
                key={nav.id}
                onClick={() => setCurrentPage(nav.id as AppPage)}
                aria-current={isActive ? 'page' : undefined}
                className={`relative w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-[#f25c24] ${
                  isActive ? 'text-white' : 'text-[#b8a495] hover:bg-[#241710] hover:text-white'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active-indicator"
                    className="absolute inset-0 bg-[#2b1c13] border border-[#f25c24]/40 rounded-xl"
                    transition={spring.soft}
                  />
                )}
                <Icon className={`w-3.5 h-3.5 ${nav.color} relative z-10`} />
                <span className="relative z-10">{nav.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer: Ollama Status */}
      <div className="p-3 border-t border-[#302016] bg-[#170e09]">
        <div className="flex items-center justify-between text-[11px] bg-[#22160f] py-1.5 px-2.5 rounded-lg border border-[#3b271d]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[#dcd1c8] font-medium">Ollama running</span>
          </div>
          <span className="text-[#8e7869] font-mono">Qwen3 4B</span>
        </div>
      </div>
    </aside>
  );
};

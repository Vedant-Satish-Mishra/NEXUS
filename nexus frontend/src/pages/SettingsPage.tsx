import React, { useEffect, useState } from 'react';
import {
  Moon,
  Sun,
  Monitor,
  Zap,
  BarChart3,
  RotateCcw,
  ShieldCheck,
  LogOut,
  Download,
  Trash2,
  Lock,
  Globe,
  Sliders,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import { SettingsService, UserSettings } from '../lib/api';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme, reducedMotion, setReducedMotion, logout } = useApp();

  const [settings, setSettings] = useState<UserSettings>({
    model_profile: 'fast',
    default_preset: 'balanced',
    memory_enabled: true,
    learning_enabled: true,
    privacy_mode: true,
    web_search_enabled: false,
    theme: 'dark',
    reduced_motion: false,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modals state
  const [showResetLearningModal, setShowResetLearningModal] = useState(false);
  const [showDeleteMemoriesModal, setShowDeleteMemoriesModal] = useState(false);
  const [showDeleteAccountModal, setShowDeleteAccountModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [confirmInput, setConfirmInput] = useState('');
  const [modalError, setModalError] = useState<string | null>(null);

  useEffect(() => {
    SettingsService.get()
      .then((res) => {
        setSettings(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleUpdate = async (updates: Partial<UserSettings>) => {
    const updated = { ...settings, ...updates };
    setSettings(updated);
    setSaving(true);
    try {
      await SettingsService.update(updated);
      setSuccessMsg('Settings saved');
      setTimeout(() => setSuccessMsg(null), 2500);
    } catch {
      // silently retain optimistic state
    } finally {
      setSaving(false);
    }
  };

  const handleExport = async () => {
    try {
      await SettingsService.downloadExport();
    } catch (err: any) {
      alert(err.message || 'Export failed');
    }
  };

  const handleResetLearning = async () => {
    try {
      await SettingsService.resetLearning();
      setShowResetLearningModal(false);
      setConfirmInput('');
      setSuccessMsg('Learning signals cleared');
      setTimeout(() => setSuccessMsg(null), 2500);
    } catch (err: any) {
      setModalError(err.message || 'Failed to reset learning');
    }
  };

  const handleDeleteMemories = async () => {
    try {
      const { MemoryService } = await import('../lib/api');
      await MemoryService.wipeAll();
      setShowDeleteMemoriesModal(false);
      setConfirmInput('');
      setSuccessMsg('All memories wiped');
      setTimeout(() => setSuccessMsg(null), 2500);
    } catch (err: any) {
      setModalError(err.message || 'Failed to wipe memories');
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      setModalError('Password is required');
      return;
    }
    try {
      await SettingsService.deleteAccount(deletePassword);
      logout();
    } catch (err: any) {
      setModalError(err.message || 'Incorrect password or deletion error');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Header */}
      <div className="p-8 border-b border-[#302016] flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Settings</h1>
          <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
            Configure system defaults, cognitive agent presets, and data sovereignty policies.
          </p>
        </div>
        {successMsg && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4" />
            <span>{successMsg}</span>
          </div>
        )}
      </div>

      <div className="p-8 space-y-6 max-w-3xl">
        {/* 1. Model Profile & VRAM Guidance */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-[#a08c7e] block">
            Cognitive Model Profile
          </label>
          <p className="text-xs text-[#8e7869]">
            Select local model profile based on your laptop's available GPU VRAM.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div
              onClick={() => handleUpdate({ model_profile: 'fast' })}
              className={`p-4 rounded-xl border flex flex-col justify-between cursor-pointer transition-all ${
                settings.model_profile === 'fast'
                  ? 'border-[#f25c24] bg-[#2d1d14] ring-1 ring-[#f25c24]'
                  : 'border-[#3d291d] bg-[#1c120a] hover:border-[#523929]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#f25c24]" />
                  <span className="font-bold text-xs text-white">Fast Profile (Default)</span>
                </div>
                {settings.model_profile === 'fast' && (
                  <span className="w-2 h-2 rounded-full bg-[#f25c24]" />
                )}
              </div>
              <div className="mt-2 space-y-0.5">
                <div className="text-xs font-semibold text-white">Qwen3 4B Instruct</div>
                <div className="text-[10px] text-[#8e7869]">
                  VRAM: ~2.6 GB | Context: 8,192 tokens | Latency: ~400ms
                </div>
              </div>
            </div>

            <div
              onClick={() => handleUpdate({ model_profile: 'quality' })}
              className={`p-4 rounded-xl border flex flex-col justify-between cursor-pointer transition-all ${
                settings.model_profile === 'quality'
                  ? 'border-[#f25c24] bg-[#2d1d14] ring-1 ring-[#f25c24]'
                  : 'border-[#3d291d] bg-[#1c120a] hover:border-[#523929]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-amber-400" />
                  <span className="font-bold text-xs text-white">Quality Profile</span>
                </div>
                {settings.model_profile === 'quality' && (
                  <span className="w-2 h-2 rounded-full bg-[#f25c24]" />
                )}
              </div>
              <div className="mt-2 space-y-0.5">
                <div className="text-xs font-semibold text-white">Qwen3 8B Q4_K_M</div>
                <div className="text-[10px] text-[#8e7869]">
                  VRAM: ~5.5 GB | Context: 6,144 tokens | Deep reasoning
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Default Preset for New Chats */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-[#a08c7e] block">
            Default Agent Preset
          </label>
          <p className="text-xs text-[#8e7869]">
            The initial agent combination selected when starting a new conversation.
          </p>

          <div className="grid grid-cols-3 gap-2 bg-[#1b120c] p-1.5 rounded-xl border border-[#3b271d]">
            {(['fast', 'balanced', 'full'] as const).map((preset) => (
              <button
                key={preset}
                onClick={() => handleUpdate({ default_preset: preset })}
                className={`py-2 rounded-lg text-xs font-semibold capitalize transition-all ${
                  settings.default_preset === preset
                    ? 'bg-[#f25c24] text-white shadow-sm'
                    : 'text-[#8e7869] hover:text-white'
                }`}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* 3. Memory Sovereignty */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                Personal Memory Agent
              </h4>
              <p className="text-xs text-[#8e7869] mt-0.5 max-w-sm">
                Recalls confirmed facts from past chats. Memories are saved strictly when you click Save.
              </p>
            </div>
            <button
              onClick={() => handleUpdate({ memory_enabled: !settings.memory_enabled })}
              className={`w-10 h-6 rounded-full p-1 flex items-center transition-colors ${
                settings.memory_enabled ? 'bg-[#f25c24] justify-end' : 'bg-[#3b271d] justify-start'
              }`}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow-md" />
            </button>
          </div>

          <div className="pt-2 border-t border-[#342217] flex items-center justify-between">
            <span className="text-xs text-[#8e7869]">Purge all episodic & long-term memories</span>
            <button
              onClick={() => {
                setConfirmInput('');
                setModalError(null);
                setShowDeleteMemoriesModal(true);
              }}
              className="text-xs text-rose-400 hover:text-rose-300 font-semibold px-3 py-1.5 rounded-lg border border-rose-900/40 hover:bg-rose-950/20 transition-colors flex items-center gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete all memories</span>
            </button>
          </div>
        </div>

        {/* 4. Adaptive Learning Agent */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Adaptive Learning</h4>
              <p className="text-xs text-[#8e7869] mt-0.5 max-w-sm">
                Adapts plan detail, retrieval source boosts, and answer style from accumulated feedback. Model weights are never modified.
              </p>
            </div>
            <button
              onClick={() => handleUpdate({ learning_enabled: !settings.learning_enabled })}
              className={`w-10 h-6 rounded-full p-1 flex items-center transition-colors ${
                settings.learning_enabled ? 'bg-[#f25c24] justify-end' : 'bg-[#3b271d] justify-start'
              }`}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow-md" />
            </button>
          </div>

          <div className="pt-2 border-t border-[#342217] flex items-center justify-between">
            <span className="text-xs text-[#8e7869]">Reset aggregated feedback signals and hints</span>
            <button
              onClick={() => {
                setConfirmInput('');
                setModalError(null);
                setShowResetLearningModal(true);
              }}
              className="text-xs text-[#dfd6ce] hover:text-white font-semibold px-3 py-1.5 rounded-lg border border-[#4a3426] hover:bg-[#2e1d14] transition-colors flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#f25c24]" />
              <span>Reset learning data</span>
            </button>
          </div>
        </div>

        {/* 5. Privacy & Web Search Invariants */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">Local-Only Mode</h4>
                <p className="text-xs text-[#8e7869]">Zero telemetry or external model calls.</p>
              </div>
            </div>
            <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded-full">
              Enforced Active
            </span>
          </div>

          <div className="pt-3 border-t border-[#342217] flex items-center justify-between opacity-75">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-[#8e7869]" />
              <div>
                <div className="text-xs font-bold text-white">Web Search Tool</div>
                <div className="text-[10px] text-[#8e7869]">
                  Off by default — Local-first policy preserves complete network isolation
                </div>
              </div>
            </div>
            <span className="text-[10px] font-semibold text-[#8e7869] bg-[#1c120a] border border-[#3d291d] px-2 py-0.5 rounded">
              Disabled
            </span>
          </div>
        </div>

        {/* 6. Appearance & Accessibility */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Theme</h4>
              <p className="text-xs text-[#8e7869]">Interface color scheme</p>
            </div>
            <div className="flex items-center gap-1.5 bg-[#1b120c] p-1 rounded-xl border border-[#3b271d]">
              <button
                onClick={() => {
                  setTheme('dark');
                  handleUpdate({ theme: 'dark' });
                }}
                className={`p-1.5 rounded-lg text-xs font-semibold ${
                  theme === 'dark' ? 'bg-[#f25c24] text-white' : 'text-[#8e7869]'
                }`}
              >
                <Moon className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setTheme('light');
                  handleUpdate({ theme: 'light' });
                }}
                className={`p-1.5 rounded-lg text-xs font-semibold ${
                  theme === 'light' ? 'bg-[#f25c24] text-white' : 'text-[#8e7869]'
                }`}
              >
                <Sun className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setTheme('system');
                  handleUpdate({ theme: 'system' });
                }}
                className={`p-1.5 rounded-lg text-xs font-semibold ${
                  theme === 'system' ? 'bg-[#f25c24] text-white' : 'text-[#8e7869]'
                }`}
              >
                <Monitor className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="pt-3 border-t border-[#342217] flex items-center justify-between">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-white">Reduced Motion</h4>
              <p className="text-xs text-[#8e7869]">Replaces spring animations with instant state transitions</p>
            </div>
            <button
              onClick={() => {
                const nextVal = !reducedMotion;
                setReducedMotion(nextVal);
                handleUpdate({ reduced_motion: nextVal });
              }}
              className={`w-10 h-6 rounded-full p-1 flex items-center transition-colors ${
                reducedMotion ? 'bg-[#f25c24] justify-end' : 'bg-[#3b271d] justify-start'
              }`}
            >
              <div className="w-4 h-4 rounded-full bg-white shadow-md" />
            </button>
          </div>
        </div>

        {/* 7. Data Portability & Account Deletion */}
        <div className="bg-[#241710] border border-[#3d291d] rounded-2xl p-6 space-y-4">
          <label className="text-xs font-bold uppercase tracking-wider text-[#a08c7e] block">
            Data Portability & Erasure
          </label>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-bold text-white">Export My Data (ZIP)</div>
              <p className="text-xs text-[#8e7869]">
                Download conversations, memories, feedback, and file metadata in a portable archive.
              </p>
            </div>
            <button
              onClick={handleExport}
              className="text-xs text-white bg-[#302016] hover:bg-[#3d291d] font-semibold px-4 py-2 rounded-xl border border-[#4a3426] transition-colors flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-[#f25c24]" />
              <span>Download ZIP</span>
            </button>
          </div>

          <div className="pt-3 border-t border-rose-950/40 flex items-center justify-between">
            <div>
              <div className="text-xs font-bold text-rose-400">Permanently Delete Account</div>
              <p className="text-xs text-[#8e7869]">
                Cascades through PostgreSQL, Chroma vectors, and uploaded disk files.
              </p>
            </div>
            <button
              onClick={() => {
                setDeletePassword('');
                setModalError(null);
                setShowDeleteAccountModal(true);
              }}
              className="text-xs text-rose-400 hover:text-rose-300 font-semibold px-4 py-2 rounded-xl border border-rose-900/40 hover:bg-rose-950/20 transition-colors"
            >
              Delete Account
            </button>
          </div>
        </div>

        {/* 8. Sign Out */}
        <div className="pt-2">
          <button
            onClick={logout}
            className="w-full border border-red-900/40 hover:bg-red-950/20 text-red-400 font-semibold text-xs py-3 rounded-2xl flex items-center justify-center gap-2 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign out</span>
          </button>
        </div>
      </div>

      {/* MODAL: Reset Learning Data */}
      {showResetLearningModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <RotateCcw className="w-4 h-4 text-[#f25c24]" />
              <span>Reset Adaptive Learning</span>
            </h3>
            <p className="text-xs text-[#8e7869] leading-relaxed">
              This will wipe all recorded feedback signals, strategy nudges, and source boost rankings. Type{' '}
              <strong className="text-white">RESET</strong> to confirm:
            </p>
            <input
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder="RESET"
              className="w-full bg-[#1b120c] border border-[#3d291d] rounded-xl px-3 py-2 text-xs text-white"
            />
            {modalError && <p className="text-xs text-rose-400">{modalError}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowResetLearningModal(false)}
                className="px-4 py-2 text-xs font-semibold text-[#8e7869] hover:text-white"
              >
                Cancel
              </button>
              <button
                disabled={confirmInput !== 'RESET'}
                onClick={handleResetLearning}
                className="px-4 py-2 text-xs font-semibold bg-[#f25c24] disabled:opacity-50 text-white rounded-xl"
              >
                Confirm Reset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Delete All Memories */}
      {showDeleteMemoriesModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#241710] border border-[#3d291d] rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>Wipe All Memories</span>
            </h3>
            <p className="text-xs text-[#8e7869] leading-relaxed">
              This will permanently delete all confirmed long-term and episodic memory vectors. Type{' '}
              <strong className="text-white">DELETE</strong> to confirm:
            </p>
            <input
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder="DELETE"
              className="w-full bg-[#1b120c] border border-[#3d291d] rounded-xl px-3 py-2 text-xs text-white"
            />
            {modalError && <p className="text-xs text-rose-400">{modalError}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowDeleteMemoriesModal(false)}
                className="px-4 py-2 text-xs font-semibold text-[#8e7869] hover:text-white"
              >
                Cancel
              </button>
              <button
                disabled={confirmInput !== 'DELETE'}
                onClick={handleDeleteMemories}
                className="px-4 py-2 text-xs font-semibold bg-rose-600 disabled:opacity-50 text-white rounded-xl"
              >
                Wipe All Memories
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Delete Account */}
      {showDeleteAccountModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#241710] border border-rose-900/50 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-rose-400" />
              <span>Confirm Account Deletion</span>
            </h3>
            <p className="text-xs text-[#8e7869] leading-relaxed">
              This action is permanent and cannot be undone. Enter your account password to confirm complete deletion:
            </p>
            <input
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="Your password"
              className="w-full bg-[#1b120c] border border-[#3d291d] rounded-xl px-3 py-2 text-xs text-white"
            />
            {modalError && <p className="text-xs text-rose-400">{modalError}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowDeleteAccountModal(false)}
                className="px-4 py-2 text-xs font-semibold text-[#8e7869] hover:text-white"
              >
                Cancel
              </button>
              <button
                disabled={!deletePassword}
                onClick={handleDeleteAccount}
                className="px-4 py-2 text-xs font-semibold bg-rose-600 disabled:opacity-50 text-white rounded-xl"
              >
                Permanently Delete Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

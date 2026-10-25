import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, ShieldAlert, Play, Edit3, XCircle, Clock, Cpu, WifiOff, FileLock2 } from 'lucide-react';

export interface PythonApprovalDialogProps {
  isOpen: boolean;
  toolId: string;
  initialCode: string;
  onDecision: (action: 'approve' | 'edit' | 'deny', editedCode?: string) => void;
}

export const PythonApprovalDialog: React.FC<PythonApprovalDialogProps> = ({
  isOpen,
  toolId,
  initialCode,
  onDecision,
}) => {
  const [code, setCode] = useState(initialCode);
  const [isEditing, setIsEditing] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCode(initialCode);
  }, [initialCode]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        onDecision('deny');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onDecision]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
        <motion.div
          ref={modalRef}
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.2 }}
          className="bg-[#20140d] border border-[#4a3426] rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl flex flex-col max-h-[90vh]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="dialog-title"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#3b271d] pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-amber-400" />
              <h2 id="dialog-title" className="font-bold text-sm text-white">
                Python Sandbox Execution Approval
              </h2>
            </div>
            <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-amber-950/60 border border-amber-800 text-amber-300">
              Needs Confirmation
            </span>
          </div>

          {/* Sandbox Limits Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#170e09] border border-[#302016] p-2.5 rounded-xl text-[10px] text-[#a08c7e]">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>10s timeout</span>
            </div>
            <div className="flex items-center gap-1.5">
              <WifiOff className="w-3.5 h-3.5 text-rose-400" />
              <span>No network</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              <span>512 MB RAM</span>
            </div>
            <div className="flex items-center gap-1.5">
              <FileLock2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>No file access</span>
            </div>
          </div>

          {/* Code Editor */}
          <div className="space-y-1.5 flex-1 min-h-[160px] flex flex-col">
            <div className="flex items-center justify-between text-xs text-[#8e7869]">
              <span>Script code to execute</span>
              <button
                type="button"
                onClick={() => setIsEditing(!isEditing)}
                className="text-[#f25c24] hover:underline flex items-center gap-1 text-[11px]"
              >
                <Edit3 className="w-3 h-3" />
                <span>{isEditing ? 'Done Editing' : 'Edit Script'}</span>
              </button>
            </div>

            <textarea
              value={code}
              readOnly={!isEditing}
              onChange={(e) => setCode(e.target.value)}
              className={`w-full flex-1 min-h-[180px] p-3 rounded-xl font-mono text-xs border transition-colors resize-none ${
                isEditing
                  ? 'bg-[#120a06] border-[#f25c24] text-amber-100 ring-1 ring-[#f25c24]'
                  : 'bg-[#150d08] border-[#342217] text-[#dfd6ce]'
              }`}
              spellCheck="false"
            />
          </div>

          {/* Security Advisory */}
          <div className="flex items-start gap-2 bg-[#1c120a] border border-[#3b271d] p-3 rounded-xl text-[11px] text-[#8e7869]">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p leading-relaxed>
              This code runs inside an isolated sub-process with restricted Linux capabilities, memory limits, and no host filesystem access.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#342217]">
            <button
              type="button"
              onClick={() => onDecision('deny')}
              className="px-4 py-2 text-xs font-semibold text-rose-400 hover:bg-rose-950/20 rounded-xl border border-rose-900/40 transition-colors flex items-center gap-1.5"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Deny</span>
            </button>

            {isEditing ? (
              <button
                type="button"
                onClick={() => onDecision('edit', code)}
                className="px-4 py-2 text-xs font-semibold bg-[#f25c24] hover:bg-[#d97706] text-white rounded-xl transition-colors flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Edit & Run</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => onDecision('approve')}
                className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-colors flex items-center gap-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run</span>
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

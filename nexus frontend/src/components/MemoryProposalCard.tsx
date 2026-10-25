import React, { useState } from 'react';
import { MemoryItem } from '../types';
import { useApp } from '../context/AppContext';
import { MessageSquare, Check, X, Edit3, Bookmark } from 'lucide-react';

interface MemoryProposalCardProps {
  memory: MemoryItem;
}

export const MemoryProposalCard: React.FC<MemoryProposalCardProps> = ({ memory }) => {
  const { saveMemory, dismissMemory } = useApp();
  const [isSaved, setIsSaved] = useState(memory.status === 'saved');
  const [isDismissed, setIsDismissed] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(memory.content);

  if (isDismissed) return null;

  return (
    <div className="bg-[#241710] border border-[#483325] rounded-2xl p-4 my-3 text-xs text-[#fbf8f2] shadow-sm animate-fade-in space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bookmark className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-bold text-amber-300 uppercase tracking-wider text-[10px]">
            Pending memory proposal
          </span>
        </div>
        <span className="text-[10px] bg-amber-500/20 text-amber-300 font-semibold px-2 py-0.5 rounded-full capitalize">
          {memory.importance}
        </span>
      </div>

      <div className="flex items-start gap-3">
        <MessageSquare className="w-4 h-4 text-[#8e7869] shrink-0 mt-0.5" />
        <div className="flex-1">
          {isEditing ? (
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              rows={2}
              className="w-full bg-[#18100a] text-white p-2 rounded-lg border border-[#4a3426] focus:outline-none focus:ring-1 focus:ring-[#f25c24] text-xs"
            />
          ) : (
            <p className="text-sm font-medium text-[#f0e6dd] leading-snug">{content}</p>
          )}
          <p className="text-[10px] text-[#8e7869] mt-1">{memory.sourceChat}</p>
        </div>
      </div>

      {isSaved ? (
        <div className="text-emerald-400 font-semibold flex items-center gap-1.5 pt-1">
          <Check className="w-3.5 h-3.5" />
          <span>Saved to confirmed memories</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 pt-1 border-t border-[#332218]">
          <button
            onClick={() => {
              saveMemory(memory.id);
              setIsSaved(true);
            }}
            className="bg-[#f25c24] hover:bg-[#d94c17] text-white font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
          >
            <Check className="w-3 h-3" />
            <span>Save</span>
          </button>

          {isEditing ? (
            <button
              onClick={() => setIsEditing(false)}
              className="bg-[#352319] hover:bg-[#432d20] text-[#e0d4cc] px-3 py-1.5 rounded-lg"
            >
              Done
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="bg-[#352319] hover:bg-[#432d20] text-[#e0d4cc] px-3 py-1.5 rounded-lg flex items-center gap-1"
            >
              <Edit3 className="w-3 h-3" />
              <span>Edit</span>
            </button>
          )}

          <button
            onClick={() => {
              dismissMemory(memory.id);
              setIsDismissed(true);
            }}
            className="text-[#8e7869] hover:text-[#fbf8f2] px-2 py-1.5 ml-auto flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            <span>Dismiss</span>
          </button>
        </div>
      )}
    </div>
  );
};

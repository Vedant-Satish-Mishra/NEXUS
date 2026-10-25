import React from 'react';
import { Understanding } from '../types';
import { Brain, Sparkles, Layers } from 'lucide-react';

interface UnderstandingCardProps {
  understanding: Understanding;
}

export const UnderstandingCard: React.FC<UnderstandingCardProps> = ({ understanding }) => {
  return (
    <div className="bg-[#241710] border border-[#3e2b20] rounded-xl p-3 my-2 text-xs text-[#fbf8f2] shadow-sm animate-fade-in">
      <div className="flex items-center gap-1.5 mb-2 text-[#a89586] font-bold uppercase tracking-wider text-[10px]">
        <Brain className="w-3.5 h-3.5 text-[#f25c24]" />
        <span>Understood</span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="bg-[#301f15] text-[#f25c24] font-medium px-2.5 py-1 rounded-md border border-[#4d3222]">
          {understanding.intent}
        </span>
        <span className="bg-[#301f15] text-[#e0d4cc] font-medium px-2.5 py-1 rounded-md border border-[#4d3222]">
          {understanding.domain}
        </span>
        {understanding.userContext.timeAvailable && (
          <span className="bg-[#301f15] text-[#e0d4cc] font-medium px-2.5 py-1 rounded-md border border-[#4d3222]">
            {understanding.userContext.timeAvailable}
          </span>
        )}
        <span className="bg-[#f25c24]/20 text-[#f25c24] font-semibold px-2.5 py-1 rounded-md border border-[#f25c24]/30 ml-auto">
          Tier {understanding.tier} — {understanding.complexity}
        </span>
      </div>
    </div>
  );
};

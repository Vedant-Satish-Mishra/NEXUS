import React from 'react';

export interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = 'h-4 w-full', count = 1 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`bg-[#2c1d14] rounded-lg relative overflow-hidden animate-pulse ${className}`}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[#3d291d]/30 to-transparent -translate-x-full animate-[shimmer_1.5s_infinite]" />
        </div>
      ))}
    </div>
  );
};

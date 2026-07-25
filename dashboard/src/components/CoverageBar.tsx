import React from 'react';

interface CoverageBarProps {
  percent: number;
}

export function CoverageBar({ percent }: CoverageBarProps) {
  if (percent === 0) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-gray-800 rounded-full h-2">
          <div className="bg-gray-600 h-2 rounded-full w-0" />
        </div>
        <span className="text-gray-500 text-xs w-10">N/A</span>
      </div>
    );
  }

  const getColor = (p: number) => {
    if (p >= 80) return "bg-green-500";
    if (p >= 50) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 bg-gray-800 rounded-full h-2 overflow-hidden shadow-inner">
        <div
          className={`${getColor(percent)} h-full rounded-full transition-all duration-700`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
      <span className="text-white text-xs w-10 text-right font-mono">
        {percent.toFixed(0)}%
      </span>
    </div>
  );
}

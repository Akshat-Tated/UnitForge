import React from 'react';
import { JobStatus } from '../types';

interface StatusBadgeProps {
  status: JobStatus;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getBadgeStyles = () => {
    switch (status) {
      case JobStatus.QUEUED:
        return 'bg-slate-800 text-slate-300 border-slate-700';
      case JobStatus.RUNNING:
        return 'bg-blue-900/40 text-blue-400 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)] animate-pulse';
      case JobStatus.DONE:
        return 'bg-emerald-900/40 text-emerald-400 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]';
      case JobStatus.FAILED:
        return 'bg-rose-900/40 text-rose-400 border-rose-500/50 shadow-[0_0_10px_rgba(225,29,72,0.2)]';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border backdrop-blur-sm transition-all duration-300 ${getBadgeStyles()}`}
    >
      {status}
    </span>
  );
};

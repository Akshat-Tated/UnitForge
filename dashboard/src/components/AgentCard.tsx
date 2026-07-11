import React from 'react';
import { JobStatus } from '../types';
import { StatusBadge } from './StatusBadge';
import { CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';

interface AgentCardProps {
  moduleName: string;
  status: JobStatus;
  coveragePercent?: number;
  passed?: boolean;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  moduleName,
  status,
  coveragePercent,
  passed,
}) => {
  const getIcon = () => {
    switch (status) {
      case JobStatus.DONE:
        return passed ? (
          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
        ) : (
          <XCircle className="w-6 h-6 text-rose-400" />
        );
      case JobStatus.FAILED:
        return <XCircle className="w-6 h-6 text-rose-400" />;
      case JobStatus.RUNNING:
        return <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />;
      case JobStatus.QUEUED:
      default:
        return <Clock className="w-6 h-6 text-slate-400" />;
    }
  };

  return (
    <div className="group flex items-center justify-between p-5 bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-xl hover:bg-slate-800/60 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-0.5">
      <div className="flex items-center gap-4">
        <div className="flex items-center justify-center w-12 h-12 bg-slate-900/50 rounded-xl shadow-inner border border-slate-700/30">
          {getIcon()}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-100 group-hover:text-white transition-colors tracking-wide">
            {moduleName}
          </h3>
          <div className="mt-1.5 flex items-center">
            <StatusBadge status={status} />
          </div>
        </div>
      </div>
      
      {coveragePercent !== undefined && (status === JobStatus.DONE || status === JobStatus.FAILED) && (
        <div className="flex flex-col items-end">
          <span className="text-xs text-slate-400 font-medium mb-1.5 uppercase tracking-wider">Coverage</span>
          <div className="flex items-center gap-3">
            <div className="w-20 h-2 bg-slate-900 rounded-full overflow-hidden shadow-inner">
              <div 
                className={`h-full rounded-full transition-all duration-1000 ${
                  coveragePercent >= 80 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 
                  coveragePercent >= 50 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 
                  'bg-rose-500 shadow-[0_0_8px_rgba(225,29,72,0.5)]'
                }`}
                style={{ width: `${coveragePercent}%` }}
              />
            </div>
            <span className={`text-lg font-bold ${
              coveragePercent >= 80 ? 'text-emerald-400' : 
              coveragePercent >= 50 ? 'text-amber-400' : 
              'text-rose-400'
            }`}>
              {coveragePercent}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

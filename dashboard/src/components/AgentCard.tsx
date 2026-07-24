import React, { useState } from 'react';
import { JobStatus } from '../types';
import { StatusBadge } from './StatusBadge';
import { CheckCircle2, XCircle, Clock, Loader2, Code2, ChevronDown, ChevronUp } from 'lucide-react';

interface AgentCardProps {
  moduleName: string;
  status: JobStatus;
  coveragePercent?: number;
  passed?: boolean;
  generatedTestCode?: string;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  moduleName,
  status,
  coveragePercent,
  passed,
  generatedTestCode,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getIcon = () => {
    switch (status) {
      case JobStatus.DONE:
        return passed ? (
          <CheckCircle2 className="w-6 h-6 text-emerald-400" />
        ) : (
          <XCircle className="w-6 h-6 text-rose-400" />
        );
      case JobStatus.FAILED:
        return <XCircle className="w-6 h-6 text-rose-400" />
      case JobStatus.RUNNING:
        return <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
      case JobStatus.QUEUED:
      default:
        return <Clock className="w-6 h-6 text-slate-400" />
    }
  };

  const renderCoverage = () => {
    if (coveragePercent === undefined) return null;
    const isNA = coveragePercent === 0.0;
    const displayValue = isNA ? 'N/A' : `${coveragePercent}%`;
    const progressValue = isNA ? 0 : coveragePercent;
    
    return (
      <div className="flex flex-col items-end">
        <span className="text-xs text-slate-400 font-medium mb-1.5 uppercase tracking-wider">Coverage</span>
        <div className="flex items-center gap-3">
          <div className="w-20 h-2 bg-slate-900 rounded-full overflow-hidden shadow-inner">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ${
                isNA ? 'bg-slate-700' :
                progressValue >= 80 ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 
                progressValue >= 50 ? 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]' : 
                'bg-rose-500 shadow-[0_0_8px_rgba(225,29,72,0.5)]'
              }`}
              style={{ width: `${progressValue}%` }}
            />
          </div>
          <span className={`text-lg font-bold ${
            isNA ? 'text-slate-500' :
            progressValue >= 80 ? 'text-emerald-400' : 
            progressValue >= 50 ? 'text-amber-400' : 
            'text-rose-400'
          }`}>
            {displayValue}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="group flex flex-col p-5 bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-xl hover:bg-slate-800/60 transition-all duration-300 shadow-[0_4px_15px_rgb(0,0,0,0.1)]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-12 h-12 bg-slate-900/50 rounded-xl shadow-inner border border-slate-700/30">
            {getIcon()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100 group-hover:text-white transition-colors tracking-wide">
              {moduleName}
            </h3>
            <div className="mt-1.5 flex items-center gap-3">
              <StatusBadge status={status} />
              {passed !== undefined && (
                <span className={`text-xs font-semibold ${passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {passed ? 'Passed' : 'Failed'}
                </span>
              )}
            </div>
          </div>
        </div>
        
        {renderCoverage()}
      </div>

      {generatedTestCode && (
        <div className="mt-5 pt-4 border-t border-slate-700/50">
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors w-full"
          >
            <Code2 className="w-4 h-4" />
            {isExpanded ? 'Hide generated tests' : 'View generated tests'}
            {isExpanded ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
          </button>
          
          {isExpanded && (
            <div className="mt-4 p-4 bg-slate-900/80 rounded-lg overflow-x-auto border border-slate-700/50">
              <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed">
                {generatedTestCode}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

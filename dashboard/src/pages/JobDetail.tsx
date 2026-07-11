import { JobStatus } from '../types';
import { AgentCard } from '../components/AgentCard';
import { ArrowLeft, Play, LayoutGrid } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

export const JobDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <header className="mb-10">
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-indigo-400 transition-colors mb-6 group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          Back to Dashboard
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <div className="p-2 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                <LayoutGrid className="w-7 h-7 text-indigo-400" />
              </div>
              Job Execution Details
            </h1>
            <p className="mt-3 text-slate-400 font-mono text-sm tracking-wide bg-slate-900/50 inline-block px-3 py-1 rounded-md border border-slate-800">
              ID: {id || '1111-2222-3333-4444'}
            </p>
          </div>
          <button className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg font-medium transition-all duration-300 shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:shadow-[0_0_25px_rgba(79,70,229,0.6)]">
            <Play className="w-4 h-4 fill-current" />
            Rerun Failed Modules
          </button>
        </div>
      </header>

      <div className="mb-8 p-6 bg-slate-800/30 border border-slate-700/50 rounded-2xl backdrop-blur-sm">
        <h2 className="text-lg font-semibold text-slate-100 mb-6 flex items-center gap-2">
          Agent Status Overview
          <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-slate-700 text-slate-300 ml-2">
            5 Modules Discovered
          </span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <AgentCard 
            moduleName="core.auth.token_service" 
            status={JobStatus.DONE} 
            coveragePercent={95} 
            passed={true} 
          />
          <AgentCard 
            moduleName="core.auth.middleware" 
            status={JobStatus.FAILED} 
            coveragePercent={45} 
            passed={false} 
          />
          <AgentCard 
            moduleName="core.auth.utils" 
            status={JobStatus.DONE} 
            coveragePercent={88} 
            passed={true} 
          />
          <AgentCard 
            moduleName="core.users.repository" 
            status={JobStatus.RUNNING} 
          />
          <AgentCard 
            moduleName="core.users.validators" 
            status={JobStatus.QUEUED} 
          />
        </div>
      </div>
    </div>
  );
};

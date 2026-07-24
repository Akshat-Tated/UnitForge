import { useState, useEffect } from 'react';
import { JobStatus, type TestJob, type TestResult } from '../types';
import { AgentCard } from '../components/AgentCard';
import { ArrowLeft, Play, LayoutGrid, Loader2, AlertCircle } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchJob, fetchJobResults } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

export const JobDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  
  const [job, setJob] = useState<TestJob | null>(null);
  const [results, setResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let intervalId: ReturnType<typeof setInterval>;

    if (!id) return;

    const loadData = async () => {
      try {
        const [jobData, resultsData] = await Promise.all([
          fetchJob(id),
          fetchJobResults(id)
        ]);
        
        if (mounted) {
          setJob(jobData);
          setResults(resultsData);
          setError(null);

          if (jobData.status === JobStatus.DONE || jobData.status === JobStatus.FAILED) {
            clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to load job details. Is the orchestrator running?');
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    loadData();
    intervalId = setInterval(loadData, 5000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, [id]);

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <button onClick={() => navigate('/')} className="flex items-center gap-2 text-sm text-slate-400 hover:text-indigo-400 mb-6 group">
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Dashboard
        </button>
        <div className="bg-rose-900/40 border border-rose-500/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center backdrop-blur-sm shadow-xl">
          <AlertCircle className="w-12 h-12 text-rose-400 mb-4" />
          <h3 className="text-xl font-semibold text-rose-100">{error}</h3>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
          <h3 className="text-lg font-medium text-slate-200 tracking-wide">Loading job details...</h3>
        </div>
      </div>
    );
  }

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
            <div className="mt-3 flex items-center gap-4">
              <p className="text-slate-400 font-mono text-sm tracking-wide bg-slate-900/50 inline-block px-3 py-1 rounded-md border border-slate-800">
                ID: {job?.id}
              </p>
              {job && <StatusBadge status={job.status} />}
            </div>
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
            {results.length} Modules Processed
          </span>
        </h2>
        
        {results.length === 0 ? (
          <div className="text-center py-10 text-slate-400">
            No modules discovered for this job yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {results.map(result => (
              <AgentCard 
                key={result.id}
                moduleName={result.moduleName} 
                status={result.passed ? JobStatus.DONE : JobStatus.FAILED} 
                coveragePercent={result.coveragePercent} 
                passed={result.passed} 
                generatedTestCode={result.generatedTestCode}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

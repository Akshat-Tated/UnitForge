import React, { useState, useEffect } from 'react';
import { type TestJob } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Activity, Calendar, GitBranch, FileCode2, ChevronRight, Loader2, AlertCircle, Inbox } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { fetchAllJobs } from '../api/client';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<TestJob[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadJobs = async () => {
      try {
        const data = await fetchAllJobs();
        if (mounted) {
          setJobs(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to load jobs. Is the orchestrator running?');
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    loadJobs();
    const intervalId = setInterval(loadJobs, 10000);

    return () => {
      mounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const totalJobs = jobs.length;
  const runningJobs = jobs.filter(j => j.status === 'RUNNING').length;
  const doneJobs = jobs.filter(j => j.status === 'DONE').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <header className="mb-12 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
              <Activity className="w-8 h-8 text-indigo-400" />
            </div>
            UnitForge
          </h1>
          <p className="mt-3 text-sm text-slate-400 font-medium tracking-wide uppercase">
            Autonomous Test Generation Dashboard
          </p>
        </div>
      </header>

      {!isLoading && !error && (
        <div className="grid grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-xl shadow-lg flex flex-col items-center justify-center transition-all hover:bg-slate-800/60">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-widest mb-2">Total Jobs</span>
            <span className="text-3xl font-bold text-white">{totalJobs}</span>
          </div>
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-xl shadow-lg flex flex-col items-center justify-center transition-all hover:bg-slate-800/60">
            <span className="text-xs font-medium text-blue-400 uppercase tracking-widest mb-2">Running</span>
            <span className="text-3xl font-bold text-blue-400">{runningJobs}</span>
          </div>
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 backdrop-blur-xl shadow-lg flex flex-col items-center justify-center transition-all hover:bg-slate-800/60">
            <span className="text-xs font-medium text-emerald-400 uppercase tracking-widest mb-2">Done</span>
            <span className="text-3xl font-bold text-emerald-400">{doneJobs}</span>
          </div>
        </div>
      )}

      {error ? (
        <div className="bg-rose-900/40 border border-rose-500/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center backdrop-blur-sm shadow-xl">
          <AlertCircle className="w-12 h-12 text-rose-400 mb-4" />
          <h3 className="text-xl font-semibold text-rose-100">{error}</h3>
          <p className="text-base text-rose-300 mt-2">Please ensure the backend is running on http://localhost:8080</p>
        </div>
      ) : isLoading ? (
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-16 flex flex-col items-center justify-center text-center backdrop-blur-xl shadow-xl">
          <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-4" />
          <h3 className="text-lg font-medium text-slate-200 tracking-wide">Loading jobs...</h3>
        </div>
      ) : jobs.length === 0 ? (
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-16 flex flex-col items-center justify-center text-center backdrop-blur-xl shadow-xl">
          <Inbox className="w-16 h-16 text-slate-500 mb-4" />
          <h3 className="text-xl font-medium text-slate-300">No jobs yet</h3>
          <p className="text-slate-500 mt-2 text-sm">Submit a new repository or OpenAPI spec to get started.</p>
        </div>
      ) : (
        <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl overflow-hidden backdrop-blur-xl shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700/50 bg-slate-800/60 text-xs uppercase tracking-widest text-slate-400">
                  <th className="px-8 py-5 font-semibold">Job Target</th>
                  <th className="px-8 py-5 font-semibold">Type</th>
                  <th className="px-8 py-5 font-semibold">Status</th>
                  <th className="px-8 py-5 font-semibold">Started At</th>
                  <th className="px-8 py-5 font-semibold text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                {jobs.map(job => (
                  <tr 
                    key={job.id} 
                    className="hover:bg-slate-700/30 transition-all duration-200 group cursor-pointer"
                    onClick={() => navigate(`/jobs/${job.id}`)}
                  >
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-4">
                        <div className="p-2.5 bg-slate-900 rounded-lg text-indigo-300 shadow-inner border border-slate-700/30">
                          <FileCode2 className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="text-base font-semibold text-slate-100 group-hover:text-white transition-colors">{job.inputPath}</div>
                          <div className="text-xs text-slate-500 font-mono mt-1">ID: {job.id.slice(0, 8)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2 text-sm text-slate-300 font-medium">
                        <GitBranch className="w-4 h-4 text-slate-500" />
                        <span className="capitalize">{job.inputType}</span>
                      </div>
                    </td>
                    <td className="px-8 py-5">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2 text-sm text-slate-400">
                        <Calendar className="w-4 h-4 opacity-70" />
                        {new Date(job.createdAt).toLocaleString(undefined, { 
                          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                        })}
                      </div>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <div className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-slate-800 text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-sm border border-slate-700/50 group-hover:border-indigo-500">
                        <ChevronRight className="w-5 h-5" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

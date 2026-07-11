import { JobStatus, TestJob } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { Activity, Calendar, GitBranch, FileCode2, ChevronRight } from 'lucide-react';

const mockJobs: TestJob[] = [
  {
    id: 'job-1111-2222',
    status: JobStatus.RUNNING,
    inputType: 'python',
    inputPath: './core/auth',
    createdAt: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
  },
  {
    id: 'job-3333-4444',
    status: JobStatus.DONE,
    inputType: 'openapi',
    inputPath: './specs/payment-api.yaml',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
  },
  {
    id: 'job-5555-6666',
    status: JobStatus.FAILED,
    inputType: 'java',
    inputPath: './src/main/java/com/billing',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(),
  }
];

export const Dashboard: React.FC = () => {
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
              {mockJobs.map(job => (
                <tr 
                  key={job.id} 
                  className="hover:bg-slate-700/30 transition-all duration-200 group cursor-pointer"
                  onClick={() => window.location.href = `/jobs/${job.id}`}
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
    </div>
  );
};

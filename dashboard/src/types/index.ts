export enum JobStatus {
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  DONE = 'DONE',
  FAILED = 'FAILED',
}

export interface TestJob {
  id: string; // UUID
  status: JobStatus;
  inputType: string;
  inputPath: string;
  createdAt: string; // ISO Date String
  updatedAt: string; // ISO Date String
}

export interface TestResult {
  id: string; // UUID or string
  jobId: string; // UUID
  moduleName: string;
  passed: boolean;
  coveragePercent: number;
  generatedTestCode: string;
  agentLog: string;
  createdAt: string; // ISO Date String
}

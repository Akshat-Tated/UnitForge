import axios from 'axios';
import type { TestJob, TestResult } from '../types';

const apiClient = axios.create({
  baseURL: 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;

export async function fetchAllJobs(): Promise<TestJob[]> {
  const response = await apiClient.get<TestJob[]>('/jobs');
  return response.data;
}

export async function fetchJob(id: string): Promise<TestJob> {
  const response = await apiClient.get<TestJob>(`/jobs/${id}`);
  return response.data;
}

export async function fetchJobResults(id: string): Promise<TestResult[]> {
  const response = await apiClient.get<TestResult[]>(`/jobs/${id}/results`);
  return response.data;
}

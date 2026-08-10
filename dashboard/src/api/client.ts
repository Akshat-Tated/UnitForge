import axios from 'axios';
import type { TestJob, TestResult } from '../types';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("unitforge_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — clear and redirect to login
      localStorage.removeItem("unitforge_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

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

export async function rerunFailedModules(
  id: string
): Promise<{ message: string; requeued: number }> {
  const response = await apiClient.post(
    `/jobs/${id}/rerun`
  );
  return response.data;
}

export async function login(
  email: string,
  password: string
): Promise<string> {
  const response = await apiClient.post<{ token: string }>("/auth/login", {
    email,
    password,
  });
  return response.data.token;
}

export async function register(
  name: string,
  email: string,
  password: string
): Promise<string> {
  const response = await apiClient.post<{ token: string }>("/auth/register", {
    name,
    email,
    password,
  });
  return response.data.token;
}

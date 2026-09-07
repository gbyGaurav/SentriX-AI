import { AnalysisResponse, HistoryResponse, HealthResponse } from '../types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function analyzeFile(file: File): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeText(text: string): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('text', text);
  const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function analyzeUrl(url: string): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append('url', url);
  const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body: formData });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalysis(id: string): Promise<AnalysisResponse> {
  const res = await fetch(`${API_URL}/api/analysis/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getHistory(page = 1, pageSize = 20): Promise<HistoryResponse> {
  const res = await fetch(`${API_URL}/api/history?page=${page}&page_size=${pageSize}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

import { AnalysisResponse, HistoryResponse, HealthResponse } from '../types';

const PRODUCTION_API_URL = 'https://sentrix-backend-rhua.onrender.com';

/**
 * Resolves the backend base URL safely across environments:
 * 1. Checks NEXT_PUBLIC_API_URL if defined and not pointing to localhost in production.
 * 2. If running in a browser on any non-localhost host (e.g. Vercel), defaults to the production Render backend.
 * 3. In production server builds, defaults to the production Render backend.
 * 4. Strips any trailing slashes to avoid '//api' issues.
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && envUrl.trim()) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    if (typeof window !== 'undefined') {
      const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      if (!isLocalHost && trimmed.includes('localhost')) {
        return PRODUCTION_API_URL;
      }
    }
    return trimmed;
  }

  if (typeof window !== 'undefined') {
    const isLocalHost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!isLocalHost) {
      return PRODUCTION_API_URL;
    }
  }

  if (process.env.NODE_ENV === 'production') {
    return PRODUCTION_API_URL;
  }

  return 'http://localhost:8000';
}

/**
 * Robust fetch wrapper with timeout and helpful descriptive error extraction.
 */
async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  // 60-second timeout to gracefully handle Render free tier cold starts
  const timeoutId = setTimeout(() => controller.abort(), 60000);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = '';
      try {
        const errorJson = await res.json();
        errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
      } catch {
        try {
          errorDetail = await res.text();
        } catch {}
      }

      if (res.status === 404) {
        throw new Error(`SentriX backend returned HTTP 404: Endpoint not found (${url}).`);
      } else if (res.status === 502 || res.status === 503) {
        throw new Error(`SentriX analysis server is temporarily unavailable (HTTP ${res.status}). The service may be waking up from cold sleep, please retry in 10 seconds.`);
      } else if (res.status === 500) {
        throw new Error(`SentriX backend error (HTTP 500): ${errorDetail || 'Internal server error'}`);
      } else {
        throw new Error(`SentriX backend returned HTTP ${res.status}: ${errorDetail || res.statusText}`);
      }
    }

    return res;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Analysis request timed out after 60s. The SentriX backend server on Render is waking up from sleep. Please try again now.');
    }
    // Network or CORS failure
    if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError') || err.message.includes('fetch failed'))) {
      const baseUrl = getApiBaseUrl();
      throw new Error(`Cannot connect to SentriX analysis server at ${baseUrl}. The server may be waking up, offline, or experiencing network connectivity issues.`);
    }
    throw err;
  }
}

export async function analyzeFile(file: File): Promise<AnalysisResponse> {
  const baseUrl = getApiBaseUrl();
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiFetch(`${baseUrl}/api/analyze`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function analyzeText(text: string): Promise<AnalysisResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await apiFetch(`${baseUrl}/api/analyze/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  return res.json();
}

export async function analyzeUrl(url: string): Promise<AnalysisResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await apiFetch(`${baseUrl}/api/analyze/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  return res.json();
}

export async function getAnalysis(id: string): Promise<AnalysisResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await apiFetch(`${baseUrl}/api/analysis/${encodeURIComponent(id)}`);
  return res.json();
}

export async function getHistory(page = 1, pageSize = 50): Promise<HistoryResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await apiFetch(`${baseUrl}/api/history?page=${page}&page_size=${pageSize}`);
  return res.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const baseUrl = getApiBaseUrl();
  const res = await apiFetch(`${baseUrl}/api/health`);
  return res.json();
}


'use client';

import { useState } from 'react';
import { AnalysisResponse } from '../types';
import { analyzeFile, analyzeText, analyzeUrl } from '../lib/api';

export function useAnalysis() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalysis = async (apiCall: () => Promise<AnalysisResponse>) => {
    setIsAnalyzing(true);
    setError(null);
    setProgress(0);
    setResult(null);

    // Simulate progress while waiting for the single API response
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) return prev;
        return prev + 10;
      });
    }, 500);

    try {
      const res = await apiCall();
      clearInterval(progressInterval);
      setProgress(100);
      setResult(res);
      return res;
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.message || 'An error occurred during analysis.');
      setIsAnalyzing(false);
      return null;
    }
  };

  const submitFile = (file: File) => handleAnalysis(() => analyzeFile(file));
  const submitText = (text: string) => handleAnalysis(() => analyzeText(text));
  const submitUrl = (url: string) => handleAnalysis(() => analyzeUrl(url));

  const reset = () => {
    setIsAnalyzing(false);
    setProgress(0);
    setResult(null);
    setError(null);
  };

  return { isAnalyzing, progress, result, error, submitFile, submitText, submitUrl, reset };
}

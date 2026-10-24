import { APP_CONFIG } from "../config";
import { CheckResponse, EstimateResponse, HealthResponse } from "../types";

const BASE_URL = APP_CONFIG.apiBaseUrl;

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchEstimate(date: string, percentile: number): Promise<EstimateResponse> {
  const res = await fetch(`${BASE_URL}/api/estimate?date=${encodeURIComponent(date)}&percentile=${percentile}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody.detail || `Estimate request failed (HTTP ${res.status})`;
    throw new Error(message);
  }
  return res.json();
}

export async function fetchCheck(date: string, percentile: number): Promise<CheckResponse> {
  const res = await fetch(`${BASE_URL}/api/check?date=${encodeURIComponent(date)}&percentile=${percentile}`);
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    const message = errorBody.detail || `Reliability check request failed (HTTP ${res.status})`;
    throw new Error(message);
  }
  return res.json();
}

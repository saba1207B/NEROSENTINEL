/**
 * Resolves the target API URL for a given endpoint path.
 *
 * 1. Server-side in Vercel Functions: Uses the internal service binding `process.env.BACKEND_URL`
 *    (injected by Vercel Services at runtime, e.g. `await fetch(new URL('api/v1/items', process.env.BACKEND_URL))`).
 * 2. Explicit public override: Uses `process.env.NEXT_PUBLIC_API_BASE_URL` if defined.
 * 3. Client-side browser on shared Vercel domain: Uses relative `/api/v1/...` on the same origin.
 * 4. Local standalone development fallback: Uses `http://127.0.0.1:8000/api/v1/...`.
 */
export function resolveApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const cleanSubpath = normalizedPath.startsWith('/api/v1')
    ? normalizedPath.replace(/^\/api\/v1/, '')
    : normalizedPath;

  if (typeof window === 'undefined' && process.env.BACKEND_URL) {
    const base = process.env.BACKEND_URL.endsWith('/')
      ? process.env.BACKEND_URL
      : `${process.env.BACKEND_URL}/`;
    const relativePart = cleanSubpath.startsWith('/') ? cleanSubpath.slice(1) : cleanSubpath;
    return new URL(`api/v1/${relativePart}`, base).toString();
  }

  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, '');
    return `${base}${cleanSubpath}`;
  }

  if (typeof window !== 'undefined') {
    return `/api/v1${cleanSubpath}`;
  }

  return `http://127.0.0.1:8000/api/v1${cleanSubpath}`;
}

export type ApiMeta = {
  source_type: string;
  synthetic?: boolean;
  data_quality_status?: string | null;
  model_version?: string | null;
  limitations?: string[];
  data_as_of?: string | null;
  region_id?: string | null;
};

export type ApiEnvelope<T> = { data: T; meta: ApiMeta };

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export function getDemoToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.sessionStorage.getItem('aquasentinel_demo_token');
}

export function setDemoToken(token: string): void {
  if (typeof window === 'undefined') return;
  if (token.trim()) window.sessionStorage.setItem('aquasentinel_demo_token', token.trim());
  else window.sessionStorage.removeItem('aquasentinel_demo_token');
}

async function request<T>(path: string, method: 'GET' | 'POST', body?: unknown, authenticated = false): Promise<ApiEnvelope<T>> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (authenticated) {
    const token = getDemoToken();
    if (!token) throw new ApiError(401, 'A demo bearer token is required. Paste one in Settings before this action.');
    headers.Authorization = `Bearer ${token}`;
  }
  const endpoint = resolveApiUrl(path);
  let response: Response;
  try {
    response = await fetch(endpoint, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    });
  } catch (error) {
    throw new ApiError(0, `Backend unreachable at ${endpoint}. Start the NeroSentinel service and check its address. ${error instanceof Error ? error.message : ''}`);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload && typeof payload === 'object' && 'error' in payload ? (payload as { error?: { message?: string } }).error?.message : undefined;
    throw new ApiError(response.status, detail || `Backend returned HTTP ${response.status}`);
  }
  if (!payload || typeof payload !== 'object' || !('data' in payload) || !('meta' in payload)) {
    throw new ApiError(response.status, 'Backend returned an unexpected response contract.');
  }
  return payload as ApiEnvelope<T>;
}

export const apiGet = <T>(path: string) => request<T>(path, 'GET');
export const apiPost = <T>(path: string, body: unknown, authenticated = false) => request<T>(path, 'POST', body, authenticated);

export type Region = { id: string; name: string; centroid: [number, number] };
export type Risk = { score: number; severity: string; uncertainty: string; factors: Record<string, number> };
export type DashboardSummary = {
  region: Region;
  enso: { phase: string; classification_basis?: string };
  water: { reservoir_storage_mcm: number; capacity_fraction: number; groundwater_index: number };
  risk: Risk;
  active_alerts: number;
};
export type Reservoir = { id: string; name: string; capacity_mcm: number; storage_mcm: number; dead_storage_mcm: number };
export type MonthlyResult = { month: number; valid_month?: string; storage_mcm: number; supply_mcm: number; demand_mcm: number; unmet_mcm: number; inflow_mcm?: number; evaporation_mcm?: number; gross_release_mcm?: number; conveyance_loss_mcm?: number };
export type ScenarioResult = { scenario_id: string; region_id: string; trajectory: MonthlyResult[]; total_unmet_mcm: number; reliability: number; mass_balance_error_mcm: number; assumptions: string[]; shortage_onset_month?: number | null };
export type Alert = { id: string; type?: string; severity?: string; status?: string; delivery_mode?: string; region_id?: string };

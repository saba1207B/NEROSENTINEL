'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, KeyRound, Shield } from 'lucide-react';
import { apiGet, getDemoToken, setDemoToken } from '@/lib/api-client';

type Source = { id: string; status: string; mode?: string };

export default function SettingsPage() {
  const [token, setToken] = useState('');
  const [saved, setSaved] = useState(false);
  useEffect(() => { const timer = window.setTimeout(() => setSaved(Boolean(getDemoToken())), 0); return () => window.clearTimeout(timer); }, []);
  const health = useQuery({ queryKey: ['backend-health'], queryFn: () => apiGet<{ status: string }>('/health'), retry: false });
  const sources = useQuery({ queryKey: ['backend-sources'], queryFn: () => apiGet<{ items: Source[] }>('/sources'), retry: false });
  function save() { setDemoToken(token); setToken(''); setSaved(Boolean(getDemoToken())); }
  function clear() { setDemoToken(''); setToken(''); setSaved(false); }
  return <div className="mx-auto max-w-4xl space-y-6 pb-12"><div><h1 className="text-2xl font-bold text-slate-900">Connection & Demo Access</h1><p className="mt-1 text-sm text-slate-500">This export has no account directory, API-key manager or production login.</p></div>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><Database className="h-5 w-5 text-brand-blue" /><h2 className="text-lg font-semibold text-slate-900">Backend status</h2></div><p className="mt-4 text-sm text-slate-700">{health.isPending ? 'Checking…' : health.error ? `Unavailable: ${health.error.message}` : `Connected · ${health.data?.data.status || 'responding'}`}</p><button onClick={() => { void health.refetch(); void sources.refetch(); }} className="mt-4 rounded-md border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700">Check again</button></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><KeyRound className="h-5 w-5 text-brand-blue" /><h2 className="text-lg font-semibold text-slate-900">Local demo bearer token</h2></div><p className="mt-3 text-sm leading-6 text-slate-600">Scenario runs and alert acknowledgements need a backend-issued token. Generate one locally with <code className="rounded bg-slate-100 px-1">python scripts/demo_token.py --role researcher</code> in the backend folder. Authority-only actions need an authority token. Tokens are kept only in this browser tab&apos;s session storage; do not use this mechanism for production identity.</p><label htmlFor="demo-token" className="mt-5 block text-sm font-medium text-slate-700">Paste token</label><div className="mt-2 flex gap-2"><input id="demo-token" type="password" autoComplete="off" value={token} onChange={(event) => setToken(event.target.value)} placeholder={saved ? 'Token saved for this tab' : 'Bearer token'} className="min-w-0 flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm" /><button onClick={save} disabled={!token.trim()} className="rounded-md bg-brand-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">Save</button><button onClick={clear} className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700">Clear</button></div><p className="mt-2 text-xs text-slate-500">{saved ? 'A token is saved for this tab. It may expire; replace it if the backend returns 401.' : 'No token saved.'}</p></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-center gap-3"><Shield className="h-5 w-5 text-brand-blue" /><h2 className="text-lg font-semibold text-slate-900">Source availability</h2></div><p className="mt-2 text-sm text-slate-500">A listed provider is not proof of an active feed.</p>{sources.error && <p role="alert" className="mt-3 text-sm text-red-700">{sources.error.message}</p>}<div className="mt-4 divide-y divide-slate-100">{sources.data?.data.items.map((source) => <div key={source.id} className="flex flex-wrap justify-between gap-2 py-3 text-sm"><span className="font-medium text-slate-800">{source.id}</span><span className="text-slate-500">{source.status.replaceAll('_', ' ')}</span></div>)}</div></section>
  </div>;
}

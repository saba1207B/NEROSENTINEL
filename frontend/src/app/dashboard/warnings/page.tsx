'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Bell } from 'lucide-react';
import { apiGet, apiPost, type Alert } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

export default function EarlyWarningCenterPage() {
  const queryClient = useQueryClient();
  const alerts = useQuery({ queryKey: ['alerts'], queryFn: () => apiGet<{ items: Alert[] }>('/alerts') });
  const acknowledge = useMutation({
    mutationFn: (id: string) => apiPost<Alert>(`/alerts/${encodeURIComponent(id)}/acknowledge`, {}, true),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });
  return <div className="mx-auto max-w-4xl space-y-6 pb-12">
    <div><h1 className="text-2xl font-bold text-slate-900">Early Warning Center</h1><p className="mt-1 text-sm text-slate-500">Local-test alert records; no SMS, email or public warning delivery</p></div>
    {alerts.error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-800">{alerts.error.message}</div>}
    {alerts.data && <DataStatus meta={alerts.data.meta} />}
    {alerts.isLoading && <p role="status" aria-live="polite" className="text-slate-500">Loading local alerts…</p>}
    {acknowledge.error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">{acknowledge.error.message}</div>}
    <div className="space-y-4">{alerts.data?.data.items.map((alert) => <div key={alert.id} className="flex gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mt-1">{alert.severity === 'high' ? <AlertTriangle className="h-6 w-6 text-amber-600" /> : <Bell className="h-6 w-6 text-brand-blue" />}</div><div className="flex-1"><div className="flex flex-wrap items-start justify-between gap-3"><h2 className="font-semibold text-slate-900">{(alert.type || 'Local threshold rule').replaceAll('_', ' ')}</h2><span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize text-slate-600">{alert.status || 'configured'}</span></div><p className="mt-2 text-sm text-slate-600">Region: {alert.region_id || 'tn-coimbatore'} · Severity: {alert.severity || 'not assigned'} · Delivery: {alert.delivery_mode || 'local test only'}</p>{alert.status !== 'acknowledged' && <button onClick={() => acknowledge.mutate(alert.id)} disabled={acknowledge.isPending} className="mt-4 rounded-md border border-slate-200 px-3 py-1.5 text-xs font-semibold text-brand-blue disabled:opacity-50">Acknowledge with authority token</button>}</div></div>)}</div>
    {alerts.data?.data.items.length === 0 && <p className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">No local alert records.</p>}
    <p className="text-xs text-slate-500">Acknowledgement requires an authority/admin bearer token entered in Settings. It records a local state change only.</p>
  </div>;
}

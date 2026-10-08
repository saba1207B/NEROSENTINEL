'use client';

import { useQuery } from '@tanstack/react-query';
import { Line, LineChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Globe, CloudRain, Info } from 'lucide-react';
import { apiGet } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

type EnsoCurrent = { phase: string; oni_last_five_c: number[]; influence_note: string; classification_basis?: string };
type EnsoHistory = { items: { month: string; oni_c: number }[] };
type ForecastList = { items: { id: string; rainfall_anomaly_pct: number; interval_pct: number[]; status: string }[] };

export default function ClimateIntelligencePage() {
  const current = useQuery({ queryKey: ['enso-current'], queryFn: () => apiGet<EnsoCurrent>('/enso/current') });
  const history = useQuery({ queryKey: ['enso-history'], queryFn: () => apiGet<EnsoHistory>('/enso/history') });
  const forecast = useQuery({ queryKey: ['forecasts'], queryFn: () => apiGet<ForecastList>('/forecasts') });
  const error = current.error || history.error || forecast.error;
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800">{error.message}</div>;
  if (!current.data || !history.data || !forecast.data) return <p role="status" aria-live="polite" className="text-slate-500">Loading climate screening data…</p>;
  const baseline = forecast.data.data.items[0];
  return <div className="mx-auto max-w-7xl space-y-6 pb-12">
    <div><h1 className="text-2xl font-bold text-slate-900">Climate Intelligence</h1><p className="mt-1 text-sm text-slate-500">ENSO context and a declared seasonal baseline, not live meteorology</p></div>
    <DataStatus meta={current.data.meta} />
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><Globe className="h-5 w-5 text-brand-blue" /><p className="mt-4 text-sm text-slate-500">ENSO phase screen</p><p className="mt-1 text-2xl font-bold capitalize text-slate-900">{current.data.data.phase.replaceAll('_', ' ')}</p><p className="mt-2 text-xs text-slate-500">Synthetic ONI-like values</p></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><CloudRain className="h-5 w-5 text-brand-blue" /><p className="mt-4 text-sm text-slate-500">Demo rainfall anomaly</p><p className="mt-1 text-2xl font-bold text-slate-900">{baseline.rainfall_anomaly_pct}%</p><p className="mt-2 text-xs text-slate-500">Constructed baseline; no measured skill</p></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><Info className="h-5 w-5 text-brand-blue" /><p className="mt-4 text-sm text-slate-500">Demo interval</p><p className="mt-1 text-2xl font-bold text-slate-900">{baseline.interval_pct.join(' to ')}%</p><p className="mt-2 text-xs text-slate-500">Not a calibrated confidence interval</p></div>
    </div>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Synthetic ENSO index history</h2><p className="mt-1 text-sm text-slate-500">Degrees Celsius anomaly · monthly labels supplied by backend</p><div className="mt-6 h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={history.data.data.items}><CartesianGrid strokeDasharray="3 3" stroke="rgb(1 71 46 / 14%)" /><XAxis dataKey="month" tickFormatter={(value: string) => value.slice(0, 7)} fontSize={12} /><YAxis unit="°C" fontSize={12} /><Tooltip contentStyle={{ backgroundColor: 'var(--cream)', borderColor: 'rgb(1 71 46 / 18%)', borderRadius: 20 }} /><Line dataKey="oni_c" name="ONI-like anomaly" stroke="var(--forest)" strokeWidth={3} dot={{ fill: 'var(--moss)' }} /></LineChart></ResponsiveContainer></div></section>
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 text-sm text-blue-950">{current.data.data.influence_note}</div>
    <DataStatus meta={forecast.data.meta} />
  </div>;
}

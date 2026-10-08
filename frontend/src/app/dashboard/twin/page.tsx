'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { apiGet, type MonthlyResult, type Reservoir } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

type Forecast = { reservoir_id: string; trajectory: MonthlyResult[]; reliability: number };
type Balance = { storage_mcm: number; release_mcm: number; spill_mcm: number; evaporation_mcm: number; mass_balance_error_mcm: number };

export default function DigitalTwinPage() {
  const reservoir = useQuery({ queryKey: ['pilot-reservoir'], queryFn: () => apiGet<{ items: Reservoir[] }>('/reservoirs/demo-reservoir-1') });
  const forecast = useQuery({ queryKey: ['pilot-twin-forecast'], queryFn: () => apiGet<Forecast>('/reservoirs/demo-reservoir-1/forecast') });
  const balance = useQuery({ queryKey: ['pilot-balance'], queryFn: () => apiGet<Balance>('/water/balance') });
  const error = reservoir.error || forecast.error || balance.error;
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800">{error.message}</div>;
  if (!reservoir.data || !forecast.data || !balance.data) return <p role="status" aria-live="polite" className="text-slate-500">Loading digital-twin calculations…</p>;
  const item = reservoir.data.data.items[0];
  return <div className="mx-auto max-w-7xl space-y-6 pb-12">
    <div><h1 className="text-2xl font-bold text-slate-900">Water Digital Twin</h1><p className="mt-1 text-sm text-slate-500">Lumped monthly model of {item.name}; no live structural telemetry</p></div>
    <DataStatus meta={forecast.data.meta} />
    <div className="grid gap-4 md:grid-cols-4">{[
      ['Initial storage', `${item.storage_mcm} MCM`], ['Capacity', `${item.capacity_mcm} MCM`], ['Modeled release', `${balance.data.data.release_mcm.toFixed(2)} MCM`], ['Mass residual', `${balance.data.data.mass_balance_error_mcm.toFixed(6)} MCM`],
    ].map(([label, value]) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-900">{value}</p></div>)}</div>
    <div className="grid gap-6 lg:grid-cols-[2fr_1fr]"><section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Six-month modeled storage</h2><div className="mt-6 h-80"><ResponsiveContainer width="100%" height="100%"><LineChart data={forecast.data.data.trajectory}><CartesianGrid strokeDasharray="3 3" stroke="rgb(1 71 46 / 14%)" /><XAxis dataKey="valid_month" tickFormatter={(value: string) => value?.slice(0, 7) || ''} fontSize={12} /><YAxis unit=" MCM" fontSize={12} /><Tooltip contentStyle={{ backgroundColor: 'var(--cream)', borderColor: 'rgb(1 71 46 / 18%)', borderRadius: 20 }} /><Line dataKey="storage_mcm" name="Storage MCM" stroke="var(--forest)" strokeWidth={3} dot={{ fill: 'var(--moss)' }} /></LineChart></ResponsiveContainer></div></section><aside className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Model boundaries</h2><p className="mt-4 text-sm leading-6 text-slate-600">The service has a synthetic catchment, reservoir capacity, demand profile and runoff coefficient. It does not ingest dam instrumentation, validate structural stress, or issue operating commands.</p><p className="mt-4 text-sm text-slate-600">Modeled demand met in {Math.round(forecast.data.data.reliability * 100)}% of these months.</p><Link href="/dashboard/simulator" className="mt-6 inline-block text-sm font-semibold text-brand-blue">Explore scenarios →</Link></aside></div>
  </div>;
}

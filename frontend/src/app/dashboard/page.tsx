'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, Droplets, Globe } from 'lucide-react';
import { apiGet, type Alert, type DashboardSummary, type MonthlyResult } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';
import { ReservoirChart } from '@/components/ReservoirChart';

export default function DashboardPage() {
  const summary = useQuery({ queryKey: ['dashboard-summary'], queryFn: () => apiGet<DashboardSummary>('/dashboard/summary') });
  const forecast = useQuery({ queryKey: ['reservoir-forecast'], queryFn: () => apiGet<{ trajectory: MonthlyResult[]; reliability: number }>('/reservoirs/demo-reservoir-1/forecast') });
  const alerts = useQuery({ queryKey: ['alerts'], queryFn: () => apiGet<{ items: Alert[] }>('/alerts') });
  const error = summary.error || forecast.error || alerts.error;
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800">{error.message}</div>;
  if (!summary.data || !forecast.data || !alerts.data) return <p role="status" aria-live="polite" className="text-slate-500">Loading the pilot command center…</p>;

  const { data, meta } = summary.data;
  const chart = forecast.data.data.trajectory.map((point) => ({
    name: point.valid_month?.slice(0, 7) || `M${point.month}`,
    storage_mcm: point.storage_mcm,
    demand_mcm: point.demand_mcm,
  }));
  const cards = [
    { label: 'ENSO screen', value: data.enso.phase.replaceAll('_', ' '), detail: 'Synthetic ONI-like input', icon: Globe },
    { label: 'Drought screening score', value: `${Math.round(data.risk.score * 100)}/100`, detail: `${data.risk.severity} · not a probability`, icon: AlertTriangle },
    { label: 'Reservoir storage', value: `${data.water.reservoir_storage_mcm.toFixed(1)} MCM`, detail: `${Math.round(data.water.capacity_fraction * 100)}% of modeled capacity`, icon: Droplets },
    { label: 'Local alert records', value: String(alerts.data.data.items.length), detail: 'Local-test only; no delivery', icon: Activity },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-6 pb-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div><h1 className="text-2xl font-bold tracking-tight text-slate-900">Climate Command Center</h1><p className="mt-1 text-sm text-slate-500">{data.region.name} · single synthetic pilot region</p></div>
        <Link href="/dashboard/simulator" className="rounded-md bg-brand-blue px-4 py-2 text-sm font-semibold text-white">Run a scenario</Link>
      </div>
      <DataStatus meta={meta} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ label, value, detail, icon: Icon }) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><Icon className="mb-4 h-5 w-5 text-brand-blue" /><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold text-slate-900">{value}</p><p className="mt-2 text-xs text-slate-500">{detail}</p></div>)}
      </div>
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Modeled reservoir trajectory</h2>
          <p className="mt-1 text-sm text-slate-500">Storage and monthly demand in million cubic metres; not an observed forecast.</p>
          <ReservoirChart data={chart} />
          <DataStatus meta={forecast.data.meta} className="mt-4" />
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">What the evidence supports</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">The drought score combines rainfall, soil moisture, reservoir storage and a dimensionless groundwater index. It is a transparent screening index, not a calibrated event probability or an automatic instruction.</p>
          <p className="mt-4 text-sm text-slate-600">The default reservoir run meets modeled demand in {Math.round(forecast.data.data.reliability * 100)}% of months. Its inputs are synthetic.</p>
          <Link href="/dashboard/warnings" className="mt-6 inline-block text-sm font-semibold text-brand-blue">Review local alerts →</Link>
        </section>
      </div>
    </div>
  );
}

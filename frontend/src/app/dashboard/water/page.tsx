'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Droplets, Search } from 'lucide-react';
import { apiGet, type Reservoir } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

type Demand = { sectors: Record<string, number>; total_mcm: number };
type Balance = { storage_mcm: number; release_mcm: number; spill_mcm: number; evaporation_mcm: number; mass_balance_error_mcm: number };

export default function WaterResourcesPage() {
  const [search, setSearch] = useState('');
  const reservoirs = useQuery({ queryKey: ['reservoirs'], queryFn: () => apiGet<{ items: Reservoir[] }>('/reservoirs') });
  const demand = useQuery({ queryKey: ['water-demand'], queryFn: () => apiGet<Demand>('/water/demand') });
  const balance = useQuery({ queryKey: ['water-balance'], queryFn: () => apiGet<Balance>('/water/balance') });
  const error = reservoirs.error || demand.error || balance.error;
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-800">{error.message}</div>;
  if (!reservoirs.data || !demand.data || !balance.data) return <p role="status" aria-live="polite" className="text-slate-500">Loading modeled water resources…</p>;
  const items = reservoirs.data.data.items.filter((item) => item.name.toLowerCase().includes(search.toLowerCase()));
  return <div className="mx-auto max-w-7xl space-y-6 pb-12">
    <div className="flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-2xl font-bold text-slate-900">Water Resources</h1><p className="mt-1 text-sm text-slate-500">One declared pilot reservoir; volumes in million cubic metres</p></div><label className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input aria-label="Search reservoirs" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search reservoirs" className="rounded-md border border-slate-200 py-2 pl-9 pr-3 text-sm" /></label></div>
    <DataStatus meta={reservoirs.data.meta} />
    <div className="grid gap-4 md:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Modeled monthly demand</p><p className="mt-2 text-2xl font-bold text-slate-900">{demand.data.data.total_mcm.toFixed(2)} MCM</p><p className="mt-2 text-xs text-slate-500">Synthetic sector coefficients</p></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Water-balance release</p><p className="mt-2 text-2xl font-bold text-slate-900">{balance.data.data.release_mcm.toFixed(2)} MCM</p><p className="mt-2 text-xs text-slate-500">Single modeled step, not real operations</p></div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">Mass-balance residual</p><p className="mt-2 text-2xl font-bold text-slate-900">{balance.data.data.mass_balance_error_mcm.toFixed(6)} MCM</p><p className="mt-2 text-xs text-slate-500">Numerical diagnostic</p></div>
    </div>
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr><th className="px-6 py-4">Reservoir</th><th className="px-6 py-4">Storage</th><th className="px-6 py-4">Capacity</th><th className="px-6 py-4">Dead storage</th><th className="px-6 py-4">Modeled fullness</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="px-6 py-4 font-semibold text-slate-900"><Droplets className="mr-2 inline h-4 w-4 text-brand-blue" />{item.name}<p className="ml-6 text-xs font-normal text-slate-500">{item.id}</p></td><td className="px-6 py-4">{item.storage_mcm} MCM</td><td className="px-6 py-4">{item.capacity_mcm} MCM</td><td className="px-6 py-4">{item.dead_storage_mcm} MCM</td><td className="px-6 py-4">{Math.round(item.storage_mcm / item.capacity_mcm * 100)}%</td></tr>)}</tbody></table>{items.length === 0 && <p className="p-6 text-sm text-slate-500">No pilot reservoir matches that search.</p>}</div>
    <Link href="/dashboard/twin" className="inline-block text-sm font-semibold text-brand-blue">Inspect the digital twin →</Link>
  </div>;
}

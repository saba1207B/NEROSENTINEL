'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AreaChart, Area, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Play, RotateCcw, ThermometerSun, Droplets } from 'lucide-react';
import { useSimulatorStore } from '@/lib/stores/simulatorStore';
import { apiPost, type ApiEnvelope, type ScenarioResult } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

type CreatedScenario = { id: string };

export default function ScenarioSimulator() {
  const { temperatureAnomaly, precipitationMultiplier, simulationMonths, setTemperatureAnomaly, setPrecipitationMultiplier, setSimulationMonths, isRunning, setIsRunning, reset } = useSimulatorStore();
  const [baseline, setBaseline] = useState<ApiEnvelope<ScenarioResult> | null>(null);
  const [scenario, setScenario] = useState<ApiEnvelope<ScenarioResult> | null>(null);
  const [error, setError] = useState('');

  async function run() {
    setError(''); setIsRunning(true);
    try {
      const input = { region_id: 'tn-coimbatore', months: simulationMonths };
      const [baseCreated, caseCreated] = await Promise.all([
        apiPost<CreatedScenario>('/scenarios', { ...input, name: 'Frontend baseline', rainfall_multiplier: 1, temperature_delta_c: 0 }, true),
        apiPost<CreatedScenario>('/scenarios', { ...input, name: 'Frontend sensitivity case', rainfall_multiplier: precipitationMultiplier, temperature_delta_c: temperatureAnomaly }, true),
      ]);
      const [baseRun, caseRun] = await Promise.all([
        apiPost<ScenarioResult>(`/scenarios/${baseCreated.data.id}/run`, {}, true),
        apiPost<ScenarioResult>(`/scenarios/${caseCreated.data.id}/run`, {}, true),
      ]);
      setBaseline(baseRun); setScenario(caseRun);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Simulation failed'); }
    finally { setIsRunning(false); }
  }
  const chart = scenario?.data.trajectory.map((point, index) => ({ month: point.valid_month?.slice(0, 7) || `M${point.month}`, scenario: point.storage_mcm, baseline: baseline?.data.trajectory[index]?.storage_mcm })) || [];
  return <div className="mx-auto max-w-7xl space-y-6 pb-12">
    <div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-bold text-slate-900">Scenario Simulator</h1><p className="mt-1 text-sm text-slate-500">Backend-computed rainfall and temperature sensitivity for the synthetic Coimbatore pilot</p></div><div className="flex gap-2"><button onClick={() => { reset(); setBaseline(null); setScenario(null); setError(''); }} className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"><RotateCcw className="h-4 w-4" /> Reset</button><button onClick={run} disabled={isRunning} className="flex items-center gap-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"><Play className="h-4 w-4" /> {isRunning ? 'Running…' : 'Run on backend'}</button></div></div>
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">A demo researcher token is required. <Link href="/dashboard/settings" className="font-semibold underline">Set it in Settings</Link>. ENSO is contextual evidence, not a direct causal input to this simulator. No release action is executed.</div>
    {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>}
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]"><section className="space-y-7 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="font-semibold text-slate-900">Declared assumptions</h2><label className="block text-sm text-slate-700"><span className="flex items-center gap-2 font-medium"><Droplets className="h-4 w-4 text-brand-blue" /> Rainfall multiplier: {precipitationMultiplier.toFixed(2)}×</span><input type="range" min="0" max="2" step="0.05" value={precipitationMultiplier} onChange={(event) => setPrecipitationMultiplier(Number(event.target.value))} className="mt-3 w-full accent-brand-blue" /><span className="text-xs text-slate-500">0 = no modeled rainfall; 1 = pilot baseline</span></label><label className="block text-sm text-slate-700"><span className="flex items-center gap-2 font-medium"><ThermometerSun className="h-4 w-4 text-amber-600" /> Temperature delta: {temperatureAnomaly.toFixed(1)}°C</span><input type="range" min="-5" max="10" step="0.5" value={temperatureAnomaly} onChange={(event) => setTemperatureAnomaly(Number(event.target.value))} className="mt-3 w-full accent-brand-blue" /></label><label className="block text-sm font-medium text-slate-700">Duration<select value={simulationMonths} onChange={(event) => setSimulationMonths(Number(event.target.value))} className="mt-2 w-full rounded-md border border-slate-200 p-2"><option value={6}>6 months</option><option value={12}>12 months</option><option value={18}>18 months</option><option value={24}>24 months</option></select></label></section>
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Modeled storage · million cubic metres</h2><p className="mt-1 text-sm text-slate-500">Both curves use the same backend digital-twin engine and duration.</p>{chart.length ? <div className="mt-5 h-80"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chart}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="month" fontSize={12} /><YAxis unit=" MCM" fontSize={12} /><Tooltip /><Area dataKey="baseline" name="Pilot baseline" stroke="#94a3b8" fill="#e2e8f0" fillOpacity={0.4} /><Area dataKey="scenario" name="Sensitivity case" stroke="#0077b6" fill="#0077b6" fillOpacity={0.2} /></AreaChart></ResponsiveContainer></div> : <div className="mt-5 flex h-80 items-center justify-center rounded-lg bg-slate-50 text-sm text-slate-500">Run a scenario to see backend results.</div>}</section></div>
    {scenario && baseline && <div className="grid gap-4 md:grid-cols-3"><div className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm text-slate-500">Baseline unmet demand</p><p className="mt-1 text-2xl font-bold">{baseline.data.total_unmet_mcm.toFixed(2)} MCM</p></div><div className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm text-slate-500">Sensitivity-case unmet demand</p><p className="mt-1 text-2xl font-bold">{scenario.data.total_unmet_mcm.toFixed(2)} MCM</p></div><div className="rounded-xl border border-slate-200 bg-white p-5"><p className="text-sm text-slate-500">Mass-balance residual</p><p className="mt-1 text-2xl font-bold">{scenario.data.mass_balance_error_mcm.toFixed(6)} MCM</p></div></div>}
    {scenario && <DataStatus meta={scenario.meta} />}
  </div>;
}

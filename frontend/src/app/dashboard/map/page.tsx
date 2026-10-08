'use client';

import { useState } from 'react';
import Link from 'next/link';
import Map, { Marker, NavigationControl, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Layers, MapPin } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiGet, type Region, type Reservoir } from '@/lib/api-client';
import { DataStatus } from '@/components/DataStatus';

const mapStyle = {
  version: 8 as const,
  sources: { osm: { type: 'raster' as const, tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } },
  layers: [{ id: 'osm-layer', type: 'raster' as const, source: 'osm' }],
};

export default function GeospatialExplorer() {
  const [popup, setPopup] = useState(false);
  const [viewState, setViewState] = useState({ longitude: 76.9558, latitude: 11.0168, zoom: 9 });
  const region = useQuery({ queryKey: ['pilot-region'], queryFn: () => apiGet<Region>('/regions/tn-coimbatore') });
  const reservoirs = useQuery({ queryKey: ['reservoirs'], queryFn: () => apiGet<{ items: Reservoir[] }>('/reservoirs') });
  const error = region.error || reservoirs.error;
  const reservoir = reservoirs.data?.data.items[0];
  const latitude = region.data?.data.centroid[0] ?? 11.0168;
  const longitude = region.data?.data.centroid[1] ?? 76.9558;
  return <div className="relative flex h-[calc(100vh-8rem)] min-h-[540px] w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
    <aside className="absolute left-4 top-4 z-10 w-80 max-w-[calc(100%-2rem)] rounded-xl border border-slate-200 bg-white/95 p-5 shadow-md backdrop-blur-md"><h1 className="flex items-center gap-2 text-lg font-bold text-slate-900"><Layers className="h-5 w-5 text-brand-blue" /> Pilot Risk Explorer</h1><p className="mt-2 text-xs text-slate-500">One synthetic Coimbatore pilot point, not a validated reservoir coordinate or official district boundary.</p>{error && <p role="alert" className="mt-3 text-sm text-red-700">{error.message}</p>}{reservoir && <div className="mt-4 rounded-lg bg-slate-50 p-3 text-sm"><p className="font-semibold text-slate-900">{reservoir.name}</p><p className="mt-1 text-slate-600">{reservoir.storage_mcm} / {reservoir.capacity_mcm} MCM modeled storage</p><Link href="/dashboard/twin" className="mt-2 inline-block font-medium text-brand-blue">Open digital twin →</Link></div>}{region.data && <DataStatus meta={region.data.meta} className="mt-4" />}<p className="mt-3 text-xs text-slate-500">Base-map tiles require internet; backend values remain local.</p></aside>
    <Map {...viewState} onMove={(event) => setViewState(event.viewState)} mapStyle={mapStyle} style={{ width: '100%', height: '100%' }}><NavigationControl position="bottom-right" />{reservoir && <Marker latitude={latitude} longitude={longitude} anchor="bottom" onClick={(event) => { event.originalEvent.stopPropagation(); setPopup(true); }}><button aria-label="Open synthetic pilot point" className="rounded-full border-2 border-white bg-brand-blue p-2 text-white shadow-md"><MapPin className="h-5 w-5" /></button></Marker>}{popup && reservoir && <Popup latitude={latitude} longitude={longitude} anchor="top" onClose={() => setPopup(false)} closeOnClick={false}><div className="p-2 text-sm text-slate-800"><strong>{reservoir.name}</strong><p>Synthetic pilot marker</p><p>Storage: {reservoir.storage_mcm} MCM</p></div></Popup>}</Map>
  </div>;
}

/*
Copyright (c) 2026 Sabareesh M (saba1207B). All Rights Reserved.

This source code is proprietary and confidential.

Unauthorized copying, redistribution, modification, or use — including
any use for artificial intelligence / machine learning training —
is strictly prohibited.

See the LICENSE and COPYRIGHT files in the repository root for full terms.
*/

import type { ApiMeta } from '@/lib/api-client';

export function DataStatus({ meta, className = '' }: { meta?: ApiMeta; className?: string }) {
  if (!meta) return null;
  const label = meta.synthetic ? 'Synthetic pilot · not live' : meta.source_type === 'unverified' ? 'Unverified input' : 'Decision-support model';
  return (
    <div className={`rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-950 ${className}`} role="note">
      <strong>{label}</strong>
      {meta.data_quality_status && <span> · {meta.data_quality_status.replaceAll('_', ' ')}</span>}
      {meta.model_version && <span> · {meta.model_version}</span>}
      {meta.limitations?.[0] && <p className="mt-1 text-amber-800">{meta.limitations[0]}</p>}
    </div>
  );
}

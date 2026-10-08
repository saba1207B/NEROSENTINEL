'use client';

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface ReservoirData {
  name: string;
  storage_mcm: number;
  demand_mcm: number;
}

export function ReservoirChart({ data }: { data: ReservoirData[] }) {
  return (
    <div className="h-72 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorLevel" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--forest)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="var(--forest)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--moss)" stopOpacity={0.42}/>
              <stop offset="95%" stopColor="var(--moss)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgb(1 71 46 / 14%)" vertical={false} />
          <XAxis 
            dataKey="name" 
            stroke="#55715e" 
            fontSize={12} 
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="#55715e" 
            fontSize={12} 
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${value}`}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--cream)', borderColor: 'rgb(1 71 46 / 18%)', borderRadius: '20px', boxShadow: 'var(--shadow-soft)' }}
            itemStyle={{ color: 'var(--forest)' }}
          />
          <Area 
            type="monotone" 
            dataKey="storage_mcm" 
            stroke="var(--forest)" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorLevel)" 
            name="Storage (MCM)"
          />
          <Area 
            type="monotone" 
            dataKey="demand_mcm" 
            stroke="var(--moss)" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorDemand)" 
            name="Monthly demand (MCM)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

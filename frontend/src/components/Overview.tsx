import React, { useMemo, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { AccountSummary } from '../types';

interface OverviewProps {
  accounts: AccountSummary[];
}

type ChartFilter = 'all' | 'flagged';

export function Overview({ accounts }: OverviewProps) {
  const [chartFilter, setChartFilter] = useState<ChartFilter>('all');

  const { low, medium, high } = useMemo(() => {
    let l = 0, m = 0, h = 0;
    accounts.forEach(a => {
      if (a.risk_band === 'Low') l++;
      else if (a.risk_band === 'Medium') m++;
      else h++;
    });
    return { low: l, medium: m, high: h };
  }, [accounts]);

  const histogramData = useMemo(() => {
    const source = chartFilter === 'flagged'
      ? accounts.filter(a => a.risk_band !== 'Low')
      : accounts;

    const bins = Array.from({ length: 10 }, (_, i) => ({
      name: `${i * 10}–${(i + 1) * 10}`,
      count: 0,
    }));
    source.forEach(a => {
      let binIndex = Math.floor(a.mcs_score / 10);
      if (binIndex >= 10) binIndex = 9;
      bins[binIndex].count++;
    });
    return bins;
  }, [accounts, chartFilter]);

  const flaggedCount = medium + high;

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 flex flex-col items-center">
          <span className="text-emerald-400 font-medium tracking-wide text-sm uppercase">Low Risk</span>
          <span className="text-4xl font-bold text-slate-100 mt-2">{low}</span>
        </div>
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6 flex flex-col items-center">
          <span className="text-amber-400 font-medium tracking-wide text-sm uppercase">Medium Risk</span>
          <span className="text-4xl font-bold text-slate-100 mt-2">{medium}</span>
        </div>
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 flex flex-col items-center">
          <span className="text-rose-400 font-medium tracking-wide text-sm uppercase">High Risk</span>
          <span className="text-4xl font-bold text-slate-100 mt-2">{high}</span>
        </div>
      </div>

      {/* Histogram */}
      <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-6 flex flex-col h-96">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-slate-200">
            MCS Score Distribution
            {chartFilter === 'flagged' && (
              <span className="ml-2 text-sm text-slate-400 font-normal">
                ({flaggedCount} flagged account{flaggedCount !== 1 ? 's' : ''})
              </span>
            )}
          </h3>
          <div className="flex bg-slate-900/60 rounded-lg p-0.5 border border-slate-700">
            <button
              onClick={() => setChartFilter('all')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                chartFilter === 'all'
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              All Accounts
            </button>
            <button
              onClick={() => setChartFilter('flagged')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                chartFilter === 'flagged'
                  ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30'
                  : 'text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              Flagged Only
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={histogramData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip 
                cursor={{ fill: 'rgba(51, 65, 85, 0.4)' }}
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                itemStyle={{ color: '#38bdf8' }}
              />
              <Bar
                dataKey="count"
                fill={chartFilter === 'flagged' ? '#f59e0b' : '#3b82f6'}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

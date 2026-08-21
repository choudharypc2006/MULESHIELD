import React, { useState, useEffect } from 'react';
import { AccountSummary, AccountDetail, RiskBand } from '../types';
import { fetchAccountDetails, submitAction } from '../api';

interface ExplorerProps {
  accounts: AccountSummary[];
}

function RiskBadge({ band }: { band: RiskBand }) {
  const colors = {
    Low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    Medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    High: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
  };
  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${colors[band]}`}>
      {band}
    </span>
  );
}

export function Explorer({ accounts }: ExplorerProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [details, setDetails] = useState<AccountDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) {
      setDetails(null);
      return;
    }
    let active = true;
    setLoading(true);
    fetchAccountDetails(selectedId)
      .then(data => {
        if (active) setDetails(data);
      })
      .catch(err => console.error(err))
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [selectedId]);

  const handleAction = async (action: 'mule' | 'clear' | 'escalate') => {
    if (!details) return;
    const oldAction = details.action;
    
    // Optimistic update
    setDetails({ ...details, action });
    setActionLoading(true);
    
    try {
      const updated = await submitAction(details.account_id, action);
      setDetails(updated);
    } catch (err) {
      console.error(err);
      // Rollback
      setDetails({ ...details, action: oldAction });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 w-full max-w-7xl mx-auto h-[80vh]">
      {/* Left Pane: List */}
      <div className="w-full md:w-1/3 flex flex-col rounded-xl border border-slate-700 bg-slate-800/40 overflow-hidden h-full shadow-lg">
        <div className="p-4 border-b border-slate-700 bg-slate-800/60 font-semibold text-slate-200">
          Accounts ({accounts.length})
        </div>
        <div className="overflow-y-auto flex-1 p-2 space-y-1">
          {accounts.map(acc => (
            <button
              key={acc.account_id}
              onClick={() => setSelectedId(acc.account_id)}
              className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors text-left ${
                selectedId === acc.account_id 
                  ? 'bg-blue-600/20 border border-blue-500/30' 
                  : 'hover:bg-slate-700/50 border border-transparent'
              }`}
            >
              <div>
                <div className="text-slate-200 font-medium">Account #{acc.account_id}</div>
                <div className="text-slate-400 text-sm">MCS: {acc.mcs_score}</div>
              </div>
              <RiskBadge band={acc.risk_band} />
            </button>
          ))}
        </div>
      </div>

      {/* Right Pane: Details */}
      <div className="w-full md:w-2/3 flex flex-col rounded-xl border border-slate-700 bg-slate-800/40 overflow-hidden h-full shadow-lg">
        {selectedId === null ? (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            Select an account to view details
          </div>
        ) : loading || !details ? (
          <div className="flex-1 p-8 space-y-6 animate-pulse">
            <div className="h-10 bg-slate-700 rounded w-1/3"></div>
            <div className="h-24 bg-slate-700 rounded"></div>
            <div className="h-32 bg-slate-700 rounded"></div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col gap-8">
            
            {/* Header */}
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                  Account #{details.account_id}
                  {details.action && (
                    <span className="px-3 py-1 text-xs font-bold rounded bg-slate-700 text-slate-200 uppercase tracking-wider shadow-inner">
                      Status: {details.action}
                    </span>
                  )}
                </h2>
                <div className="flex items-center gap-4 mt-4">
                  <div className="text-5xl font-black text-slate-100">{details.mcs_score}</div>
                  <RiskBadge band={details.risk_band} />
                </div>
              </div>
            </div>

            {/* Sub-scores */}
            <div className="grid grid-cols-2 gap-4">
               <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700 shadow-sm">
                 <div className="text-sm text-slate-400 font-medium mb-1">Rule Signal</div>
                 <div className="text-2xl font-bold text-slate-200">{details.rule_signal}</div>
                 <div className="text-xs text-slate-500 mt-2">50% weight in MCS</div>
               </div>
               <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-700 shadow-sm">
                 <div className="text-sm text-slate-400 font-medium mb-1">ML Signal</div>
                 <div className="text-2xl font-bold text-slate-200">{details.ml_signal}</div>
                 <div className="text-xs text-slate-500 mt-2">50% weight in MCS</div>
               </div>
            </div>

            {/* Rules */}
            <div>
              <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Triggered Rules</h3>
              {details.triggered_rules.length === 0 ? (
                <div className="text-slate-400 italic">No rules triggered.</div>
              ) : (
                <ul className="space-y-3">
                  {details.triggered_rules.map(rule => (
                    <li key={rule.rule_id} className="p-4 rounded bg-slate-800 border border-slate-700 flex flex-col sm:flex-row sm:items-start gap-4 shadow-sm">
                      <div className="flex-shrink-0 mt-1">
                        <span className={`px-2 py-1 text-xs font-bold rounded ${
                          rule.severity === 'HIGH' ? 'bg-red-900/50 text-red-400' : 'bg-orange-900/50 text-orange-400'
                        }`}>
                          {rule.rule_id}
                        </span>
                      </div>
                      <div className="text-slate-300 text-sm flex-1 leading-relaxed">
                        {rule.explanation}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Explainability */}
            <div>
              <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700 pb-2">Why Flagged (ML Explanation)</h3>
              {details.top_shap_contributions.length === 0 ? (
                <div className="text-slate-400 italic">No significant flags.</div>
              ) : (
                <ul className="list-disc pl-5 space-y-2 text-slate-300 text-sm">
                  {details.top_shap_contributions.map((msg, i) => (
                    <li key={i} className="leading-relaxed">{msg}</li>
                  ))}
                </ul>
              )}
            </div>

            {/* Actions */}
            <div className="mt-auto pt-6 border-t border-slate-700">
              <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase tracking-wider">Take Action</h3>
              <div className="flex gap-4">
                <button
                  disabled={actionLoading || details.action === 'mule'}
                  onClick={() => handleAction('mule')}
                  className="flex-1 py-3 rounded-lg font-medium bg-red-600/20 text-red-400 border border-red-600/30 hover:bg-red-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Confirm Mule
                </button>
                <button
                  disabled={actionLoading || details.action === 'escalate'}
                  onClick={() => handleAction('escalate')}
                  className="flex-1 py-3 rounded-lg font-medium bg-amber-600/20 text-amber-400 border border-amber-600/30 hover:bg-amber-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Escalate
                </button>
                <button
                  disabled={actionLoading || details.action === 'clear'}
                  onClick={() => handleAction('clear')}
                  className="flex-1 py-3 rounded-lg font-medium bg-emerald-600/20 text-emerald-400 border border-emerald-600/30 hover:bg-emerald-600/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Clear Account
                </button>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AccountSummary, AccountDetail, RiskBand, NetworkGraph } from '../types';
import { fetchAccountDetails, submitAction, fetchNetwork } from '../api';
import ForceGraph3D from 'react-force-graph-3d';

interface ExplorerProps {
  accounts: AccountSummary[];
}

function RiskBadge({ band }: { band: RiskBand }) {
  const badgeClass = {
    Low: 'badge-low',
    Medium: 'badge-med',
    High: 'badge-high badge-high-pulse', // Pulse for High Risk
  }[band];
  
  return (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${badgeClass}`}>
      {band}
    </span>
  );
}

// Helper for counting animation
function CountUp({ value }: { value: number }) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    let start = 0;
    const duration = 1000;
    const startTime = performance.now();
    
    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutQuart
      const ease = 1 - Math.pow(1 - progress, 4);
      setCount(value * ease);
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setCount(value);
      }
    };
    
    requestAnimationFrame(animate);
  }, [value]);
  
  // Format based on integer vs float
  return <span>{value % 1 === 0 ? Math.round(count) : count.toFixed(1)}</span>;
}

export function Explorer({ accounts }: ExplorerProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [details, setDetails] = useState<AccountDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [network, setNetwork] = useState<NetworkGraph | null>(null);
  const [networkLoading, setNetworkLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) {
      setDetails(null);
      setNetwork(null);
      return;
    }
    let active = true;
    setLoading(true);
    setNetworkLoading(true);
    
    fetchAccountDetails(selectedId)
      .then(data => {
        if (active) setDetails(data);
      })
      .catch(err => console.error(err))
      .finally(() => {
        if (active) setLoading(false);
      });
      
    fetchNetwork(selectedId)
      .then(data => {
        if (active) setNetwork(data);
      })
      .catch(err => {
        console.error(err);
        if (active) setNetwork(null);
      })
      .finally(() => {
        if (active) setNetworkLoading(false);
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
      <div className="w-full md:w-1/3 flex flex-col rounded-xl glass-panel overflow-hidden h-full shadow-lg">
        <div className="p-4 border-b border-slate-700/50 bg-slate-800/40 font-semibold text-slate-200">
          Accounts ({accounts.length})
        </div>
        <div className="overflow-y-auto flex-1 p-2 space-y-1">
          {accounts.map(acc => {
            const isSelected = selectedId === acc.account_id;
            const itemClass = {
              Low: 'account-item-low',
              Medium: 'account-item-med',
              High: 'account-item-high',
            }[acc.risk_band];
            
            return (
              <button
                key={acc.account_id}
                onClick={() => setSelectedId(acc.account_id)}
                className={`w-full flex items-center justify-between p-3 rounded-lg text-left account-item ${itemClass} ${isSelected ? 'active' : ''}`}
              >
                <div>
                  <div className="text-slate-200 font-medium leading-tight">Account #{acc.account_id}</div>
                  <div className="text-slate-400 text-sm mt-0.5 font-medium">MCS: {acc.mcs_score}</div>
                </div>
                <RiskBadge band={acc.risk_band} />
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Pane: Details */}
      <div className="w-full md:w-2/3 flex flex-col rounded-xl glass-panel overflow-hidden h-full relative shadow-lg">
        <AnimatePresence mode="wait">
          {selectedId === null ? (
            <motion.div 
              key="empty"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex-1 flex items-center justify-center text-slate-400 font-medium"
            >
              Select an account to view details
            </motion.div>
          ) : loading || !details ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex-1 p-8 space-y-6 animate-pulse"
            >
              <div className="h-10 bg-slate-700/50 rounded w-1/3"></div>
              <div className="h-24 bg-slate-700/50 rounded"></div>
              <div className="h-32 bg-slate-700/50 rounded"></div>
            </motion.div>
          ) : (
            <motion.div 
              key="details"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col gap-8"
            >
              
              {/* Header */}
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                    Account #{details.account_id}
                    {details.action && (
                      <span className="px-3 py-1 text-xs font-bold rounded bg-slate-700/60 border border-slate-600/50 text-slate-200 uppercase tracking-wider shadow-inner">
                        Status: {details.action}
                      </span>
                    )}
                  </h2>
                  <div className="flex items-center gap-4 mt-4">
                    <div className="text-5xl font-black text-slate-100 tracking-tight">
                      <CountUp value={details.mcs_score} />
                    </div>
                    <RiskBadge band={details.risk_band} />
                  </div>
                </div>
              </div>

              {/* Sub-scores */}
              <div className="grid grid-cols-2 gap-4">
                 <div className="p-4 rounded-lg bg-slate-900/40 border border-slate-700/50 shadow-sm">
                   <div className="text-sm text-slate-400 font-semibold mb-1 uppercase tracking-wider">Rule Signal</div>
                   <div className="text-2xl font-bold text-slate-200"><CountUp value={details.rule_signal} /></div>
                   <div className="text-xs text-slate-500 mt-2">50% weight in MCS</div>
                 </div>
                 <div className="p-4 rounded-lg bg-slate-900/40 border border-slate-700/50 shadow-sm">
                   <div className="text-sm text-slate-400 font-semibold mb-1 uppercase tracking-wider">ML Signal</div>
                   <div className="text-2xl font-bold text-slate-200"><CountUp value={details.ml_signal} /></div>
                   <div className="text-xs text-slate-500 mt-2">50% weight in MCS</div>
                 </div>
              </div>

              {/* Rules */}
              <div>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700/50 pb-2">Triggered Rules</h3>
                {details.triggered_rules.length === 0 ? (
                  <div className="text-slate-400 italic">No rules triggered.</div>
                ) : (
                  <ul className="space-y-3">
                    {details.triggered_rules.map((rule, index) => (
                      <motion.li 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 + index * 0.08, ease: 'easeOut' }}
                        key={rule.rule_id} 
                        className="p-4 rounded-lg bg-slate-900/40 border border-slate-700/50 flex flex-col sm:flex-row sm:items-start gap-4 shadow-sm"
                      >
                        <div className="flex-shrink-0 mt-1">
                          <span className={`px-2 py-1 text-xs font-bold rounded ${
                            rule.severity === 'HIGH' ? 'bg-red-900/50 text-red-400 border border-red-500/20' : 'bg-orange-900/50 text-orange-400 border border-orange-500/20'
                          }`}>
                            {rule.rule_id}
                          </span>
                        </div>
                        <div className="text-slate-300 text-sm flex-1 leading-relaxed">
                          {rule.explanation}
                        </div>
                      </motion.li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Explainability */}
              <div>
                <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700/50 pb-2">Why Flagged (ML Explanation)</h3>
                {details.top_shap_contributions.length === 0 ? (
                  <div className="text-slate-400 italic">No significant flags.</div>
                ) : (
                  <ul className="list-disc pl-5 space-y-2 text-slate-300 text-sm">
                    {details.top_shap_contributions.map((msg, i) => (
                      <motion.li 
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.25 + i * 0.08, ease: 'easeOut' }}
                        key={i} 
                        className="leading-relaxed"
                      >
                        {msg}
                      </motion.li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Network Graph */}
              {!networkLoading && network && network.edges.length > 0 && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 border-b border-slate-700/50 pb-2">Account Network</h3>
                  <div className="rounded-xl overflow-hidden border border-slate-700/50 bg-[#00000033]" style={{ height: '400px' }}>
                    <ForceGraph3D
                      graphData={network}
                      nodeId="account_id"
                      nodeLabel={(node: any) => `Account #${node.account_id}`}
                      nodeColor={(node: any) => {
                        if (node.risk_band === 'High') return '#f87171';
                        if (node.risk_band === 'Medium') return '#fbbf24';
                        return '#34d399';
                      }}
                      nodeVal={(node: any) => Math.max(2, (node.mcs_score || 0) / 5)}
                      linkColor={() => 'rgba(148, 163, 184, 0.4)'}
                      linkWidth={(link: any) => link.weight * 2}
                      onNodeClick={(node: any) => setSelectedId(node.account_id)}
                      backgroundColor="rgba(0,0,0,0)"
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-3 text-center italic">
                    Accounts connected via transaction history — larger, redder nodes indicate higher risk.
                  </p>
                </motion.div>
              )}

              {/* Actions */}
              <div className="mt-auto pt-6 border-t border-slate-700/50">
                <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase tracking-wider">Take Action</h3>
                <div className="flex gap-4">
                  <button
                    disabled={actionLoading || details.action === 'mule'}
                    onClick={() => handleAction('mule')}
                    className="flex-1 py-3 rounded-lg font-semibold bg-red-600/10 text-red-400 border border-red-600/30 hover:bg-red-600/20 hover:border-red-500/50 hover:shadow-[0_0_15px_rgba(248,113,113,0.1)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    Confirm Mule
                  </button>
                  <button
                    disabled={actionLoading || details.action === 'escalate'}
                    onClick={() => handleAction('escalate')}
                    className="flex-1 py-3 rounded-lg font-semibold bg-amber-600/10 text-amber-400 border border-amber-600/30 hover:bg-amber-600/20 hover:border-amber-500/50 hover:shadow-[0_0_15px_rgba(251,191,36,0.1)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    Escalate
                  </button>
                  <button
                    disabled={actionLoading || details.action === 'clear'}
                    onClick={() => handleAction('clear')}
                    className="flex-1 py-3 rounded-lg font-semibold bg-emerald-600/10 text-emerald-400 border border-emerald-600/30 hover:bg-emerald-600/20 hover:border-emerald-500/50 hover:shadow-[0_0_15px_rgba(52,211,153,0.1)] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    Clear Account
                  </button>
                </div>
              </div>

            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

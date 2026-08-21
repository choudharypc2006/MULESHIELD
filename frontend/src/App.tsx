import { useEffect, useState } from 'react';
import { Overview } from './components/Overview';
import { Explorer } from './components/Explorer';
import { fetchAccounts } from './api';
import { AccountSummary } from './types';

type View = 'overview' | 'explorer';

function App() {
  const [view, setView] = useState<View>('overview');
  const [accounts, setAccounts] = useState<AccountSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchAccounts()
      .then(data => {
        if (active) {
          setAccounts(data);
          setError(null);
        }
      })
      .catch(err => {
        console.error(err);
        if (active) setError('Failed to load accounts. Ensure backend is running.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              MULESHIELD
            </h1>
            <span className="text-sm text-slate-400 hidden sm:inline-block border-l border-slate-700 pl-4">
              Mule-Account Risk Intelligence Platform
            </span>
          </div>
          <nav className="flex gap-2">
            <button
              onClick={() => setView('overview')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                view === 'overview' 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setView('explorer')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                view === 'explorer' 
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Explorer
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {loading ? (
          <div className="flex justify-center items-center h-[60vh]">
            <div className="animate-pulse flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
              <div className="text-slate-400">Loading risk intelligence data...</div>
            </div>
          </div>
        ) : error ? (
          <div className="flex justify-center items-center h-[60vh]">
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-6 rounded-xl max-w-lg text-center">
              <p className="font-semibold mb-2">Connection Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        ) : view === 'overview' ? (
          <Overview accounts={accounts} />
        ) : (
          <Explorer accounts={accounts} />
        )}
      </main>
    </div>
  );
}

export default App;

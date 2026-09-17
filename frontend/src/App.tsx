import { useEffect, useState } from 'react'
import axios from 'axios'
import { Server, Database, Shield, Activity, Terminal, AlertTriangle } from 'lucide-react'
import KnowledgeBasePanel from './components/KnowledgeBasePanel'
import SearchTestPanel from './components/SearchTestPanel'
import ModelsTestPanel from './components/ModelsTestPanel'
import AgentWorkspacePanel from './components/AgentWorkspacePanel'

interface SystemStatus {
  ollama_connected: boolean;
  qdrant_connected: boolean;
  models_available: string[];
  sovereign_offline?: boolean;
  active_tasks_count?: number;
  pending_approvals_count?: number;
  system_errors?: string[];
}

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'agent' | 'knowledge' | 'models'>('agent');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/system/status');
        setStatus(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to connect to SOVRA Backend API (port 8000). Ensure backend is running locally.');
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-industrial-base text-industrial-text p-4 md:p-6 font-sans antialiased">
      {/* System Alert Banner if Backend or Local Services Disconnected */}
      {error && (
        <div className="bg-red-950/50 border border-red-800/80 text-red-300 text-xs font-mono px-4 py-2.5 rounded-sm mb-4 flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>SYSTEM ALERT: {error}</span>
        </div>
      )}

      {status?.system_errors && status.system_errors.length > 0 && !error && (
        <div className="bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs font-mono px-4 py-2 rounded-sm mb-4 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>DIAGNOSTIC NOTICE: {status.system_errors.join(' | ')}</span>
        </div>
      )}

      <header className="mb-6 flex flex-col md:flex-row md:items-end justify-between border-b border-industrial-border pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold tracking-tight text-white flex items-center gap-3">
            <Shield className="w-8 h-8 text-industrial-accent" />
            SOVRA
          </h1>
          <p className="text-xs text-industrial-muted mt-1 uppercase tracking-widest font-mono">
            Sovereign Operations & Reasoning Agent · 100% Local & Air-Gapped
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-4 text-xs font-mono uppercase">
          {/* Sovereign Mode Indicator */}
          <div className="flex flex-col items-end">
            <span className="text-industrial-muted mb-1 text-[10px]">ENVIRONMENT</span>
            <div className="flex items-center space-x-2 bg-industrial-surface px-3 py-1 rounded-sm border border-industrial-border">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-emerald-400 font-bold tracking-wider">AIRGAPPED_LOCAL</span>
            </div>
          </div>
          
          {/* Ollama Status */}
          <div className="flex flex-col items-end">
            <span className="text-industrial-muted mb-1 text-[10px]">LOCAL LLM</span>
            <div className="flex items-center space-x-2 bg-industrial-surface px-3 py-1 rounded-sm border border-industrial-border">
              <Server className="w-3.5 h-3.5 text-industrial-muted" />
              {status?.ollama_connected ? (
                <span className="text-emerald-400 font-bold">ONLINE ({status.models_available.length})</span>
              ) : (
                <span className="text-red-400 font-bold">OFFLINE</span>
              )}
            </div>
          </div>
          
          {/* Qdrant Vector DB Status */}
          <div className="flex flex-col items-end">
            <span className="text-industrial-muted mb-1 text-[10px]">VECTOR DB</span>
            <div className="flex items-center space-x-2 bg-industrial-surface px-3 py-1 rounded-sm border border-industrial-border">
              <Database className="w-3.5 h-3.5 text-industrial-muted" />
              {status?.qdrant_connected ? (
                <span className="text-emerald-400 font-bold">SYNCED</span>
              ) : (
                <span className="text-red-400 font-bold">OFFLINE</span>
              )}
            </div>
          </div>

          {/* Pending Approval Badge if any */}
          {Boolean(status?.pending_approvals_count && status.pending_approvals_count > 0) && (
            <div className="flex flex-col items-end">
              <span className="text-industrial-muted mb-1 text-[10px]">HUMAN GATE</span>
              <div className="flex items-center space-x-1.5 bg-amber-950/60 px-3 py-1 rounded-sm border border-amber-700/80 animate-pulse">
                <span className="text-amber-400 font-bold">{status?.pending_approvals_count} PENDING</span>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)]">
        {/* Left Side: Navigation & Security Perimeter (Span 2) */}
        <div className="col-span-1 lg:col-span-2 flex flex-col space-y-6">
          <nav className="flex flex-col space-y-2">
            <button 
              onClick={() => setActiveTab('agent')}
              className={`flex items-center gap-3 px-4 py-3 rounded-sm border-l-4 transition-colors font-mono text-xs uppercase tracking-wider
                ${activeTab === 'agent' 
                  ? 'border-industrial-accent bg-industrial-surface text-white' 
                  : 'border-transparent text-industrial-muted hover:bg-industrial-panel hover:text-white'}`}
            >
              <Terminal className="w-4 h-4 text-industrial-accent" />
              Agent Console
            </button>
            <button 
              onClick={() => setActiveTab('knowledge')}
              className={`flex items-center gap-3 px-4 py-3 rounded-sm border-l-4 transition-colors font-mono text-xs uppercase tracking-wider
                ${activeTab === 'knowledge' 
                  ? 'border-industrial-accent bg-industrial-surface text-white' 
                  : 'border-transparent text-industrial-muted hover:bg-industrial-panel hover:text-white'}`}
            >
              <Database className="w-4 h-4" />
              Knowledge Base
            </button>
            <button 
              onClick={() => setActiveTab('models')}
              className={`flex items-center gap-3 px-4 py-3 rounded-sm border-l-4 transition-colors font-mono text-xs uppercase tracking-wider
                ${activeTab === 'models' 
                  ? 'border-industrial-accent bg-industrial-surface text-white' 
                  : 'border-transparent text-industrial-muted hover:bg-industrial-panel hover:text-white'}`}
            >
              <Activity className="w-4 h-4" />
              Model Registry
            </button>
          </nav>
          
          <div className="flex-1"></div>
          
          {/* Security Perimeter Panel */}
          <div className="bg-industrial-surface border border-industrial-border p-4 rounded-sm text-xs font-mono space-y-2.5">
            <div className="text-[11px] text-gray-400 font-bold uppercase border-b border-industrial-border pb-1.5 flex items-center justify-between">
              <span>Security Perimeter</span>
              <Shield className="w-3 h-3 text-industrial-accent" />
            </div>
            <div className="space-y-1.5 text-[11px]">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">External APIs</span>
                <span className="text-emerald-400 font-bold">100% BLOCKED</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Network Egress</span>
                <span className="text-emerald-400 font-bold">DISABLED</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Code Sandbox</span>
                <span className="text-amber-400 font-bold">DOCKER NONE</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Evidence Gate</span>
                <span className="text-emerald-400 font-bold">ACTIVE (0.35)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Approval Expiry</span>
                <span className="text-gray-300 font-mono">30 MINUTES</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Main Content (Span 10) */}
        <div className="col-span-1 lg:col-span-10 overflow-hidden flex flex-col h-full bg-industrial-panel border border-industrial-border rounded-sm">
          {activeTab === 'agent' && <AgentWorkspacePanel />}
          {activeTab === 'knowledge' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 h-full overflow-y-auto">
              <KnowledgeBasePanel />
              <SearchTestPanel />
            </div>
          )}
          {activeTab === 'models' && (
            <div className="p-6 h-full overflow-y-auto">
              <ModelsTestPanel />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App

import { useEffect, useState } from 'react'
import axios from 'axios'
import KnowledgeBasePanel from './components/KnowledgeBasePanel'
import SearchTestPanel from './components/SearchTestPanel'
import ModelsTestPanel from './components/ModelsTestPanel'
import AgentWorkspacePanel from './components/AgentWorkspacePanel'

interface SystemStatus {
  ollama_connected: boolean;
  qdrant_connected: boolean;
  models_available: string[];
}

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('agent');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('http://localhost:8000/system/status');
        setStatus(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to connect to SOVRA Backend API.');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-industrial-dark text-industrial-text p-8">
      <header className="mb-8 flex items-center justify-between border-b border-industrial-border pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SOVRA Workspace</h1>
          <p className="text-sm text-gray-400 mt-1">Sovereign Operations & Reasoning Agent</p>
        </div>
        <div className="flex items-center space-x-3 bg-industrial-panel px-4 py-2 rounded-lg border border-industrial-border">
          <div className="h-3 w-3 rounded-full bg-industrial-success animate-pulse"></div>
          <span className="font-semibold text-industrial-success tracking-wide">SOVEREIGN MODE: ACTIVE</span>
        </div>
      </header>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6">
        <button 
          onClick={() => setActiveTab('agent')}
          className={`px-4 py-2 rounded font-bold tracking-wider ${activeTab === 'agent' ? 'bg-orange-600 text-white' : 'bg-industrial-panel text-gray-400 hover:text-white'}`}
        >
          AGENT WORKSPACE
        </button>
        <button 
          onClick={() => setActiveTab('knowledge')}
          className={`px-4 py-2 rounded font-bold tracking-wider ${activeTab === 'knowledge' ? 'bg-orange-600 text-white' : 'bg-industrial-panel text-gray-400 hover:text-white'}`}
        >
          KNOWLEDGE BASE
        </button>
        <button 
          onClick={() => setActiveTab('models')}
          className={`px-4 py-2 rounded font-bold tracking-wider ${activeTab === 'models' ? 'bg-orange-600 text-white' : 'bg-industrial-panel text-gray-400 hover:text-white'}`}
        >
          MODELS
        </button>
      </div>

      <main className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: System Status */}
        <div className="col-span-1 space-y-6">
          <div className="bg-industrial-panel p-6 rounded-xl border border-industrial-border shadow-lg">
            <h2 className="text-xl font-semibold mb-4 border-b border-industrial-border pb-2">Security & Infrastructure</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">External AI APIs:</span>
                <span className="font-mono text-industrial-success">0 (BLOCKED)</span>
              </div>
              <div className="flex justify-between items-center mt-4 pt-2 border-t border-industrial-border">
                <span className="text-gray-400">Local Model (Ollama):</span>
                {status?.ollama_connected ? (
                  <span className="text-industrial-success font-mono">ACTIVE</span>
                ) : (
                  <span className="text-industrial-error font-mono">DISCONNECTED</span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Knowledge Base (Qdrant):</span>
                {status?.qdrant_connected ? (
                  <span className="text-industrial-success font-mono">ACTIVE</span>
                ) : (
                  <span className="text-industrial-warning font-mono">PENDING DB</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Content */}
        <div className="col-span-1 lg:col-span-3">
          {activeTab === 'agent' && <AgentWorkspacePanel />}
          {activeTab === 'knowledge' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <KnowledgeBasePanel />
              <SearchTestPanel />
            </div>
          )}
          {activeTab === 'models' && <ModelsTestPanel />}
        </div>
      </main>
    </div>
  )
}

export default App

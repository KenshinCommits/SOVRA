import { useState, useEffect } from 'react';
import { Cpu, Loader2, ChevronRight } from 'lucide-react';

export default function ModelsTestPanel() {
  const [models, setModels] = useState<any[]>([]);
  const [prompt, setPrompt] = useState("");
  const [routeResult, setRouteResult] = useState<any>(null);
  const [genResult, setGenResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/models")
      .then(res => res.json())
      .then(data => setModels(data))
      .catch(err => console.error("Error fetching models:", err));
  }, []);

  const handleRouteTest = async () => {
    setLoading(true);
    setRouteResult(null);
    try {
      const res = await fetch("http://localhost:8000/models/route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, has_images: false })
      });
      const data = await res.json();
      setRouteResult(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleGenerateTest = async () => {
    setLoading(true);
    setGenResult(null);
    try {
      const res = await fetch("http://localhost:8000/models/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      setGenResult(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div className="bg-industrial-surface border border-industrial-border rounded-sm p-5">
      <h2 className="text-sm font-display font-bold text-white uppercase tracking-wide mb-4 pb-2 border-b border-industrial-border">
        Model Router & Test
      </h2>
      
      {/* Registered models */}
      <div className="mb-5">
        <h3 className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-2">Registered Models</h3>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-1.5">
          {models.map(m => (
            <div
              key={m.name}
              className="flex items-center gap-2 bg-industrial-base border border-industrial-border rounded-sm px-2.5 py-1.5 text-[11px] hover:border-gray-500 transition-colors"
              title={m.capabilities.description}
            >
              <Cpu className="w-3 h-3 text-gray-600 shrink-0" />
              <span className="font-mono text-gray-300 truncate">{m.name}</span>
              <span className="text-[9px] text-gray-600 ml-auto shrink-0">{m.capabilities.modality}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Prompt */}
      <textarea
        className="w-full bg-industrial-base border border-industrial-border rounded-sm p-3 text-sm text-gray-200 placeholder-gray-600 focus:border-industrial-accent transition-colors mb-3 resize-none"
        rows={3}
        placeholder="Enter a prompt to test routing…"
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
      />

      <div className="flex gap-2 mb-5">
        <button
          onClick={handleRouteTest}
          disabled={loading || !prompt.trim()}
          className="flex items-center gap-1.5 px-3 py-2 bg-industrial-base border border-industrial-border hover:border-industrial-accent text-xs font-mono uppercase text-gray-300 rounded-sm disabled:opacity-40 transition-colors"
        >
          <ChevronRight className="w-3 h-3" />
          Route Only
        </button>
        <button
          onClick={handleGenerateTest}
          disabled={loading || !prompt.trim()}
          className="flex items-center gap-1.5 px-3 py-2 bg-industrial-accent hover:bg-industrial-accent-hover text-black text-xs font-mono font-bold uppercase rounded-sm disabled:opacity-40 transition-colors"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <ChevronRight className="w-3 h-3" />}
          Route & Generate
        </button>
      </div>

      {/* Route result */}
      {routeResult && (
        <div className="bg-industrial-base border border-industrial-border rounded-sm p-3 mb-3">
          <h3 className="text-[10px] font-mono text-sky-500 uppercase tracking-wider mb-2">Routing Decision</h3>
          <div className="text-[12px] space-y-1">
            <div className="flex gap-2">
              <span className="text-gray-600 font-mono">Selected:</span>
              <span className="text-white font-mono font-medium">{routeResult.selected_model}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-600 font-mono">Reason:</span>
              <span className="text-gray-400">{routeResult.reason}</span>
            </div>
            <div className="mt-1.5 text-[10px] text-gray-600 font-mono">
              Fingerprint: {JSON.stringify(routeResult.task_fingerprint)}
            </div>
          </div>
        </div>
      )}

      {/* Gen result */}
      {genResult && (
        <div className="bg-industrial-base border border-industrial-border rounded-sm p-3">
          <h3 className="text-[10px] font-mono text-emerald-500 uppercase tracking-wider mb-2">Generation Result</h3>
          <div className="text-[12px] space-y-1 mb-2">
            <div className="flex gap-2">
              <span className="text-gray-600 font-mono">Model:</span>
              <span className="text-white font-mono font-medium">{genResult.model_used}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-600 font-mono">Reason:</span>
              <span className="text-gray-400">{genResult.routing_reason}</span>
            </div>
          </div>
          <div className="bg-black/30 border border-industrial-border rounded-sm p-3 text-[12px] text-gray-300 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
            {genResult.response}
          </div>
        </div>
      )}
    </div>
  );
}

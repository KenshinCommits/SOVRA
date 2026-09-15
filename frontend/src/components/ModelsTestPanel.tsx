import React, { useState, useEffect } from 'react';

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
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700 text-gray-100">
      <h2 className="text-xl font-bold mb-4 text-purple-400">Model Router & Test</h2>
      
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Registered Models</h3>
        <div className="flex flex-wrap gap-2">
          {models.map(m => (
            <span key={m.name} className="px-2 py-1 bg-gray-700 rounded text-xs" title={m.capabilities.description}>
              {m.name} ({m.capabilities.modality})
            </span>
          ))}
        </div>
      </div>

      <textarea
        className="w-full bg-gray-900 border border-gray-600 rounded p-3 text-sm focus:outline-none focus:border-purple-500 mb-3"
        rows={4}
        placeholder="Enter a prompt to test routing..."
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
      />

      <div className="flex gap-3 mb-6">
        <button
          onClick={handleRouteTest}
          disabled={loading || !prompt.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded font-medium disabled:opacity-50"
        >
          Test Route Only
        </button>
        <button
          onClick={handleGenerateTest}
          disabled={loading || !prompt.trim()}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded font-medium disabled:opacity-50"
        >
          Route & Generate
        </button>
      </div>

      {routeResult && (
        <div className="bg-gray-900 p-4 rounded text-sm mb-4">
          <h3 className="font-bold text-blue-400 mb-2">Routing Decision</h3>
          <p><strong>Selected:</strong> {routeResult.selected_model}</p>
          <p><strong>Reason:</strong> {routeResult.reason}</p>
          <div className="mt-2 text-xs text-gray-400">
            <p>Fingerprint: {JSON.stringify(routeResult.task_fingerprint)}</p>
          </div>
        </div>
      )}

      {genResult && (
        <div className="bg-gray-900 p-4 rounded text-sm">
          <h3 className="font-bold text-green-400 mb-2">Generation Result</h3>
          <p className="mb-2"><strong className="text-gray-300">Model Used:</strong> {genResult.model_used}</p>
          <p className="mb-4"><strong className="text-gray-300">Reason:</strong> {genResult.routing_reason}</p>
          <div className="bg-gray-800 p-3 rounded whitespace-pre-wrap">
            {genResult.response}
          </div>
        </div>
      )}
    </div>
  );
}

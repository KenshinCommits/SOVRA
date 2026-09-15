import { useState } from 'react';
import axios from 'axios';

export default function SearchTestPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/knowledge/search', {
        query: query,
        top_k: 3
      });
      setResults(response.data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-industrial-panel p-6 rounded-xl border border-industrial-border shadow-lg mt-6">
      <h2 className="text-xl font-semibold mb-4 border-b border-industrial-border pb-2">RAG Retrieval Test</h2>
      
      <div className="flex gap-2 mb-4">
        <input 
          type="text" 
          className="flex-1 bg-industrial-dark border border-industrial-border rounded px-4 py-2 text-industrial-text focus:outline-none focus:border-industrial-accent"
          placeholder="Search knowledge base..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button 
          onClick={handleSearch}
          disabled={loading}
          className="bg-industrial-accent text-industrial-dark px-4 py-2 rounded font-semibold hover:bg-blue-400 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="text-industrial-error mb-4">{error}</div>}

      <div className="space-y-4">
        {results.map((res, i) => (
          <div key={i} className="bg-industrial-dark p-4 rounded border border-industrial-border">
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-bold text-industrial-accent bg-blue-900/30 px-2 py-1 rounded">
                {res.filename}
              </span>
              <span className="text-xs text-gray-500 font-mono">Score: {res.score.toFixed(3)}</span>
            </div>
            <div className="text-xs text-gray-400 flex gap-4 mb-2">
              {res.page !== null && <span>Page: {res.page}</span>}
              {res.section && <span>Section: {res.section}</span>}
              <span>Chunk ID: {res.chunk_index}</span>
            </div>
            <p className="text-sm text-gray-300">{res.text}</p>
          </div>
        ))}
        {!loading && results.length === 0 && query && !error && (
          <div className="text-gray-500 text-sm">No results found.</div>
        )}
      </div>
    </div>
  );
}

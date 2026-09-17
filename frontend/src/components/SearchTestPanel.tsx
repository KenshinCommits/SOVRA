import { useState } from 'react';
import axios from 'axios';
import { Search, Loader2 } from 'lucide-react';

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
    <div className="bg-industrial-surface border border-industrial-border rounded-sm p-5">
      <h2 className="text-sm font-display font-bold text-white uppercase tracking-wide mb-4 pb-2 border-b border-industrial-border">
        RAG Retrieval Test
      </h2>
      
      <div className="flex gap-2 mb-4">
        <input 
          type="text" 
          className="flex-1 bg-industrial-base border border-industrial-border rounded-sm px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-industrial-accent transition-colors"
          placeholder="Search knowledge base…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button 
          onClick={handleSearch}
          disabled={loading}
          className="flex items-center gap-1.5 bg-industrial-accent hover:bg-industrial-accent-hover text-black px-3 py-2 rounded-sm text-xs font-mono font-bold uppercase disabled:opacity-50 transition-colors"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
          Search
        </button>
      </div>

      {error && <div className="text-xs text-red-400 mb-3 font-mono">{error}</div>}

      <div className="space-y-2">
        {results.map((res, i) => (
          <div key={i} className="bg-industrial-base border border-industrial-border rounded-sm p-3">
            <div className="flex justify-between items-start mb-1.5">
              <span className="text-[11px] font-mono text-industrial-accent font-medium">
                {res.filename}
              </span>
              <span className="text-[10px] text-gray-600 font-mono">
                score: {res.score.toFixed(3)}
              </span>
            </div>
            <div className="text-[10px] text-gray-600 font-mono flex gap-3 mb-1.5">
              {res.page !== null && <span>pg {res.page}</span>}
              {res.section && <span>§ {res.section}</span>}
              <span>chunk #{res.chunk_index}</span>
            </div>
            <p className="text-[12px] text-gray-400 leading-relaxed">{res.text}</p>
          </div>
        ))}
        {!loading && results.length === 0 && query && !error && (
          <div className="text-gray-600 text-xs font-mono py-4 text-center">No results.</div>
        )}
      </div>
    </div>
  );
}

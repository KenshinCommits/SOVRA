import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Upload, Loader2, CheckCircle2, FileText, Trash2, RefreshCw } from 'lucide-react';

interface IndexedDoc {
  document_id: string;
  filename: string;
  chunks_count: number;
}

export default function KnowledgeBasePanel() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<IndexedDoc[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const res = await axios.get('http://localhost:8000/documents');
      setDocuments(res.data.documents || []);
    } catch (err) {
      console.error('Failed to fetch indexed documents', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (file: File) => {
    if (file.size > 25 * 1024 * 1024) {
      setError("File exceeds maximum allowed size limit of 25 MB.");
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
      fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await axios.delete(`http://localhost:8000/documents/${docId}`);
      fetchDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete document');
    }
  };

  return (
    <div className="bg-industrial-surface border border-industrial-border rounded-sm p-5 space-y-6">
      <div>
        <h2 className="text-sm font-display font-bold text-white uppercase tracking-wide mb-4 pb-2 border-b border-industrial-border flex items-center justify-between">
          <span>Document Ingestion (Sovereign RAG)</span>
          <span className="text-[10px] font-mono text-gray-500 font-normal">MAX 25MB</span>
        </h2>
        
        <div 
          className="border border-dashed border-industrial-border rounded-sm p-6 text-center cursor-pointer hover:border-industrial-accent hover:bg-amber-950/5 transition-colors"
          onClick={() => fileInputRef.current?.click()}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            accept=".pdf,.txt,.docx,.md" 
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleUpload(e.target.files[0]);
              }
            }}
          />
          <Upload className="w-6 h-6 mx-auto mb-2 text-gray-600" />
          <p className="text-xs text-gray-400">
            <span className="text-industrial-accent font-medium">Select file</span> to upload and index
          </p>
          <p className="text-[10px] text-gray-600 font-mono mt-1">SUPPORTED: PDF · TXT · DOCX · MD</p>
        </div>

        {uploading && (
          <div className="mt-3 flex items-center gap-2 text-xs text-amber-400 font-mono">
            <Loader2 className="w-3 h-3 animate-spin" />
            Parsing, embedding, and indexing in local Qdrant collection…
          </div>
        )}
        
        {error && (
          <div className="mt-3 text-xs text-red-400 bg-red-950/30 border border-red-900 p-2 rounded-sm font-mono">
            {error}
          </div>
        )}
        
        {result && (
          <div className="mt-3 bg-emerald-950/20 border border-emerald-900 p-3 rounded-sm">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-xs font-bold text-emerald-400">Indexed Successfully</span>
            </div>
            <div className="text-[11px] text-gray-400 font-mono space-y-0.5">
              <div>Document ID: <span className="text-gray-300">{result.document_id}</span></div>
              <div>Filename: <span className="text-gray-300">{result.filename}</span></div>
              <div>Indexed Chunks: <span className="text-gray-300">{result.chunks_indexed}</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Indexed Documents Table */}
      <div className="border-t border-industrial-border pt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-display font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-industrial-accent" />
            Indexed Knowledge Corpus ({documents.length})
          </h3>
          <button 
            onClick={fetchDocuments} 
            disabled={loadingDocs}
            className="text-[10px] font-mono text-gray-500 hover:text-gray-300 flex items-center gap-1 transition-colors"
          >
            <RefreshCw className={`w-2.5 h-2.5 ${loadingDocs ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="text-xs text-gray-600 font-mono italic p-3 border border-industrial-border/50 rounded-sm bg-industrial-base/30">
            No indexed documents found in local vector database.
          </div>
        ) : (
          <div className="border border-industrial-border rounded-sm overflow-hidden bg-industrial-base/40">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-industrial-surface border-b border-industrial-border text-[10px] text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="py-2 px-3">Filename</th>
                  <th className="py-2 px-3 text-center">Chunks</th>
                  <th className="py-2 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-industrial-border/50">
                {documents.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-industrial-panel/50 transition-colors">
                    <td className="py-2 px-3 text-gray-300 font-medium truncate max-w-[180px]">
                      {doc.filename}
                    </td>
                    <td className="py-2 px-3 text-center text-gray-400">
                      {doc.chunks_count}
                    </td>
                    <td className="py-2 px-3 text-right">
                      <button 
                        onClick={() => handleDelete(doc.document_id)}
                        className="text-red-500/80 hover:text-red-400 p-1 rounded transition-colors"
                        title="Delete document"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

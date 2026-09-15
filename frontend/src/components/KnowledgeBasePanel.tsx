import { useState, useRef } from 'react';
import axios from 'axios';

export default function KnowledgeBasePanel() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
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
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-industrial-panel p-6 rounded-xl border border-industrial-border shadow-lg">
      <h2 className="text-xl font-semibold mb-4 border-b border-industrial-border pb-2">Knowledge Base Ingestion</h2>
      
      <div 
        className="border-2 border-dashed border-industrial-border rounded-lg p-8 text-center cursor-pointer hover:border-industrial-accent transition-colors"
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept=".pdf,.txt,.docx,.csv,.xlsx" 
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleUpload(e.target.files[0]);
            }
          }}
        />
        <div className="text-gray-400 mb-2">
          <svg className="mx-auto h-12 w-12 mb-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="font-semibold text-industrial-accent">Click to upload</span> or drag and drop
        </div>
        <p className="text-xs text-gray-500">PDF, TXT, DOCX, CSV, XLSX</p>
      </div>

      {uploading && <div className="mt-4 text-industrial-warning">Processing and indexing document...</div>}
      
      {error && <div className="mt-4 text-industrial-error bg-red-900/20 p-3 rounded">{error}</div>}
      
      {result && (
        <div className="mt-4 text-sm bg-green-900/20 text-industrial-success p-3 rounded">
          <p className="font-bold">Successfully Indexed!</p>
          <p>Document ID: <span className="font-mono">{result.document_id}</span></p>
          <p>Chunks created: <span className="font-mono">{result.chunks_indexed}</span></p>
        </div>
      )}
    </div>
  );
}

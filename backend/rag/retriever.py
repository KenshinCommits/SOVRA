from typing import List, Dict, Any
from .qdrant_service import QdrantService
from .embeddings import LocalEmbeddingProvider
import os

class Retriever:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.embedding_provider = LocalEmbeddingProvider()
        self.qdrant_service = QdrantService(
            url=qdrant_url, 
            embedding_provider=self.embedding_provider
        )

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top_k context chunks.
        Returns a list of dicts with score, text, and metadata (filename, page, etc.)
        """
        results = self.qdrant_service.search(query, limit=top_k)
        
        formatted_results = []
        for res in results:
            payload = res['payload']
            formatted_results.append({
                "score": res['score'],
                "text": payload.get('text', ''),
                "filename": payload.get('filename', ''),
                "page": payload.get('page'),
                "section": payload.get('section'),
                "document_id": payload.get('document_id'),
                "chunk_index": payload.get('chunk_index')
            })
            
        return formatted_results

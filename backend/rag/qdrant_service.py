from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
from .embeddings import EmbeddingProvider

class QdrantService:
    def __init__(self, url: str, embedding_provider: EmbeddingProvider, collection_name: str = "sovra_knowledge"):
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.embedding_provider.dimension, distance=Distance.COSINE),
                )
        except Exception as e:
            print(f"Error ensuring Qdrant collection: {e}")

    def index_chunks(self, chunks: List[Any]):
        points = []
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_provider.embed_batch(texts)
        
        for idx, chunk in enumerate(chunks):
            payload = {
                "document_id": chunk.document_id,
                "filename": chunk.filename,
                "text": chunk.text,
                "page": chunk.page,
                "section": chunk.section,
                "chunk_index": chunk.chunk_index
            }
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Use hash of chunk_id as integer ID or generate UUID. Qdrant supports UUID strings.
            import uuid
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))
            
            points.append(PointStruct(
                id=point_id,
                vector=embeddings[idx],
                payload=payload
            ))
            
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        query_vector = self.embedding_provider.embed_text(query)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True
        ).points
        
        return [
            {
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

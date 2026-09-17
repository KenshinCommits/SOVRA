from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any, Optional
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

    def search(self, query: str, limit: int = 5, score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        query_vector = self.embedding_provider.embed_text(query)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True
        ).points
        
        return [
            {
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

    def delete_document(self, document_id: str):
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=2000,
                with_payload=True,
                with_vectors=False
            )
            docs = {}
            for r in records:
                p = r.payload or {}
                doc_id = p.get("document_id")
                if doc_id:
                    if doc_id not in docs:
                        docs[doc_id] = {
                            "document_id": doc_id,
                            "filename": p.get("filename", "Unknown"),
                            "chunks_count": 0
                        }
                    docs[doc_id]["chunks_count"] += 1
            return list(docs.values())
        except Exception as e:
            print(f"Error fetching documents from Qdrant: {e}")
            return []

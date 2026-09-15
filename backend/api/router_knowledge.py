from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
import uuid
import tempfile
import shutil

from backend.ingestion.parsers import DocumentParser
from backend.ingestion.chunker import TextChunker
from backend.rag.retriever import Retriever

router = APIRouter()
retriever = Retriever()
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save temp file
        ext = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name

        document_id = str(uuid.uuid4())
        
        # Parse and extract segments
        segments = DocumentParser.parse_file(temp_path)
        
        # Chunking
        chunks = chunker.chunk_segments(document_id, file.filename, segments)
        
        # Index in Qdrant
        retriever.qdrant_service.index_chunks(chunks)
        
        # Cleanup
        os.unlink(temp_path)
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "chunks_indexed": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/search")
async def search_knowledge(query: SearchQuery):
    try:
        results = retriever.retrieve_context(query.query, top_k=query.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    # Placeholder: currently we aren't tracking full document metadata in a DB
    # In a full implementation, this would query a sqlite/postgres DB.
    # For MVP Phase 2, we return an empty list or mock data, as Qdrant doesn't easily list unique docs without scrolling.
    return {"documents": []}

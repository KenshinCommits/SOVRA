from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import uuid
import tempfile
import shutil
import logging

from backend.ingestion.parsers import DocumentParser
from backend.ingestion.chunker import TextChunker
from backend.rag.retriever import Retriever

logger = logging.getLogger(__name__)

router = APIRouter()
retriever = Retriever()
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)

MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, description="The search query text")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    score_threshold: Optional[float] = Field(0.30, ge=0.0, le=1.0, description="Minimum similarity score")

class UploadResponse(BaseModel):
    status: str
    document_id: str
    filename: str
    chunks_indexed: int

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int

class DeleteResponse(BaseModel):
    status: str
    document_id: str

class DocumentItem(BaseModel):
    document_id: str
    filename: str
    chunks_count: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentItem]

@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate filename and extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty"
        )
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 2. Check file size safely during stream read
    temp_path = None
    try:
        total_size = 0
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_path = temp_file.name
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB"
                    )
                temp_file.write(chunk)

        document_id = str(uuid.uuid4())
        
        # 3. Parse and extract segments
        try:
            segments = DocumentParser.parse_file(temp_path)
        except Exception as e:
            logger.warning(f"Failed to parse document '{file.filename}': {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse document: {str(e) or 'Corrupted or unreadable file content'}"
            )
        
        if not segments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text content found in uploaded document"
            )

        # 4. Chunking
        chunks = chunker.chunk_segments(document_id, file.filename, segments)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to generate semantic chunks from document content"
            )
        
        # 5. Index in Qdrant
        retriever.qdrant_service.index_chunks(chunks)
        
        return UploadResponse(
            status="success",
            document_id=document_id,
            filename=file.filename,
            chunks_indexed=len(chunks)
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass

@router.post("/knowledge/search", response_model=SearchResponse)
async def search_knowledge(query: SearchQuery):
    try:
        results = retriever.retrieve_context(
            query.query, 
            top_k=query.top_k, 
            score_threshold=query.score_threshold
        )
        return SearchResponse(
            results=results,
            total=len(results)
        )
    except Exception as e:
        logger.exception("Error executing knowledge search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute knowledge search on local vector database"
        )

@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    try:
        retriever.qdrant_service.delete_document(document_id)
        return DeleteResponse(status="deleted", document_id=document_id)
    except Exception as e:
        logger.exception(f"Error deleting document {document_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    try:
        docs = retriever.qdrant_service.get_indexed_documents()
        return DocumentListResponse(
            documents=[DocumentItem(**d) for d in docs]
        )
    except Exception as e:
        logger.exception("Error listing indexed documents")
        return DocumentListResponse(documents=[])

from typing import List, Optional
from pydantic import BaseModel
from .parsers import DocumentSegment

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_index: int

class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_segments(self, document_id: str, filename: str, segments: List[DocumentSegment]) -> List[DocumentChunk]:
        chunks = []
        chunk_idx = 0
        
        for segment in segments:
            text = segment.text
            if not text:
                continue
                
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                chunks.append(DocumentChunk(
                    chunk_id=f"{document_id}_{chunk_idx}",
                    document_id=document_id,
                    filename=filename,
                    text=chunk_text,
                    page=segment.page,
                    section=segment.section,
                    chunk_index=chunk_idx
                ))
                
                chunk_idx += 1
                start += (self.chunk_size - self.chunk_overlap)
                
        return chunks

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
                
            text_len = len(text)
            start = 0
            while start < text_len:
                target_end = min(start + self.chunk_size, text_len)
                end = target_end
                
                # If not at the end of the text, look for natural boundary (newline, period, space)
                if end < text_len:
                    break_pos = -1
                    for delim in ["\n\n", "\n", ". ", " "]:
                        pos = text.rfind(delim, start + int(self.chunk_size * 0.7), end)
                        if pos != -1:
                            break_pos = pos + len(delim)
                            break
                    if break_pos != -1:
                        end = break_pos
                
                chunk_text = text[start:end].strip()
                if chunk_text:
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
                
                # Move start forward
                step = max(1, (end - start) - self.chunk_overlap)
                if end >= text_len:
                    break
                start += step
                # Align start to next word boundary
                while start < text_len and not text[start].isspace() and start > 0 and not text[start-1].isspace():
                    start += 1
                while start < text_len and text[start].isspace():
                    start += 1
                
        return chunks

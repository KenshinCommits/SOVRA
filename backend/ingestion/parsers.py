import os
from pypdf import PdfReader
from docx import Document as DocxDocument
import pandas as pd
from pydantic import BaseModel
from typing import List, Optional

class DocumentSegment(BaseModel):
    text: str
    page: Optional[int] = None
    section: Optional[str] = None

class DocumentParser:
    @staticmethod
    def parse_pdf(file_path: str) -> List[DocumentSegment]:
        segments = []
        reader = PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                segments.append(DocumentSegment(text=text.strip(), page=i+1))
        return segments

    @staticmethod
    def parse_docx(file_path: str) -> List[DocumentSegment]:
        segments = []
        doc = DocxDocument(file_path)
        current_section = None
        current_text = []
        
        for p in doc.paragraphs:
            if p.style.name.startswith('Heading'):
                if current_text:
                    segments.append(DocumentSegment(text="\\n".join(current_text).strip(), section=current_section))
                    current_text = []
                current_section = p.text
            elif p.text.strip():
                current_text.append(p.text.strip())
                
        if current_text:
            segments.append(DocumentSegment(text="\\n".join(current_text).strip(), section=current_section))
            
        return segments

    @staticmethod
    def parse_txt(file_path: str) -> List[DocumentSegment]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [DocumentSegment(text=f.read().strip())]

    @staticmethod
    def parse_csv(file_path: str) -> List[DocumentSegment]:
        df = pd.read_csv(file_path)
        text = df.to_csv(index=False)
        return [DocumentSegment(text=text.strip(), section="Table Data")]

    @staticmethod
    def parse_xlsx(file_path: str) -> List[DocumentSegment]:
        df = pd.read_excel(file_path)
        text = df.to_csv(index=False)
        return [DocumentSegment(text=text.strip(), section="Table Data")]

    @classmethod
    def parse_file(cls, file_path: str) -> List[DocumentSegment]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return cls.parse_pdf(file_path)
        elif ext == '.docx':
            return cls.parse_docx(file_path)
        elif ext == '.txt':
            return cls.parse_txt(file_path)
        elif ext == '.csv':
            return cls.parse_csv(file_path)
        elif ext == '.xlsx':
            return cls.parse_xlsx(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

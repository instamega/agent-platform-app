"""
Enhanced Document Processing with Better PDF Extraction
Provides robust text extraction from various document formats
"""

import os
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

# PDF processing libraries (fallback chain)
try:
    import pdfplumber
    PDF_PROCESSOR = "pdfplumber"
except ImportError:
    try:
        import pymupdf as fitz
        PDF_PROCESSOR = "pymupdf"
    except ImportError:
        import PyPDF2
        PDF_PROCESSOR = "pypdf2"

logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Metadata extracted from document"""
    filename: str
    file_type: str
    page_count: Optional[int] = None
    title: Optional[str] = None
    author: Optional[str] = None
    creation_date: Optional[str] = None
    total_chars: int = 0
    total_words: int = 0
    
class EnhancedDocumentProcessor:
    """Enhanced document processor with multiple extraction methods"""
    
    def __init__(self, preserve_formatting: bool = True):
        self.preserve_formatting = preserve_formatting
        logger.info(f"Initialized DocumentProcessor with {PDF_PROCESSOR}")
    
    def extract_text_and_metadata(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract text and metadata from document"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.pdf':
            return self._extract_pdf(file_path)
        elif file_ext in ['.md', '.txt']:
            return self._extract_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _extract_pdf(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract text from PDF using best available method"""
        filename = os.path.basename(file_path)
        
        if PDF_PROCESSOR == "pdfplumber":
            return self._extract_pdf_pdfplumber(file_path)
        elif PDF_PROCESSOR == "pymupdf":
            return self._extract_pdf_pymupdf(file_path)
        else:
            return self._extract_pdf_pypdf2(file_path)
    
    def _extract_pdf_pdfplumber(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract PDF using pdfplumber (best quality)"""
        try:
            with pdfplumber.open(file_path) as pdf:
                filename = os.path.basename(file_path)
                
                # Extract metadata
                metadata = DocumentMetadata(
                    filename=filename,
                    file_type="pdf",
                    page_count=len(pdf.pages),
                    title=pdf.metadata.get('Title'),
                    author=pdf.metadata.get('Author'),
                    creation_date=str(pdf.metadata.get('CreationDate', ''))
                )
                
                # Extract text page by page with structure preservation
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up text while preserving structure
                        page_text = self._clean_extracted_text(page_text)
                        if self.preserve_formatting:
                            pages_text.append(f"=== Page {i+1} ===\n{page_text}")
                        else:
                            pages_text.append(page_text)
                
                full_text = "\n\n".join(pages_text)
                metadata.total_chars = len(full_text)
                metadata.total_words = len(full_text.split())
                
                return full_text, metadata
                
        except Exception as e:
            logger.error(f"Error extracting PDF with pdfplumber: {e}")
            # Fallback to PyPDF2
            return self._extract_pdf_pypdf2(file_path)
    
    def _extract_pdf_pymupdf(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract PDF using PyMuPDF/fitz"""
        try:
            doc = fitz.open(file_path)
            filename = os.path.basename(file_path)
            
            # Extract metadata
            pdf_metadata = doc.metadata
            metadata = DocumentMetadata(
                filename=filename,
                file_type="pdf",
                page_count=doc.page_count,
                title=pdf_metadata.get('title'),
                author=pdf_metadata.get('author'),
                creation_date=pdf_metadata.get('creationDate', '')
            )
            
            # Extract text
            pages_text = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    page_text = self._clean_extracted_text(page_text)
                    if self.preserve_formatting:
                        pages_text.append(f"=== Page {page_num+1} ===\n{page_text}")
                    else:
                        pages_text.append(page_text)
            
            doc.close()
            
            full_text = "\n\n".join(pages_text)
            metadata.total_chars = len(full_text)
            metadata.total_words = len(full_text.split())
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting PDF with PyMuPDF: {e}")
            # Fallback to PyPDF2
            return self._extract_pdf_pypdf2(file_path)
    
    def _extract_pdf_pypdf2(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract PDF using PyPDF2 (fallback)"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                filename = os.path.basename(file_path)
                
                # Extract metadata
                pdf_info = reader.metadata if reader.metadata else {}
                metadata = DocumentMetadata(
                    filename=filename,
                    file_type="pdf",
                    page_count=len(reader.pages),
                    title=pdf_info.get('/Title'),
                    author=pdf_info.get('/Author'),
                    creation_date=str(pdf_info.get('/CreationDate', ''))
                )
                
                # Extract text
                pages_text = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        page_text = self._clean_extracted_text(page_text)
                        if self.preserve_formatting:
                            pages_text.append(f"=== Page {i+1} ===\n{page_text}")
                        else:
                            pages_text.append(page_text)
                
                full_text = "\n\n".join(pages_text)
                metadata.total_chars = len(full_text)
                metadata.total_words = len(full_text.split())
                
                return full_text, metadata
                
        except Exception as e:
            logger.error(f"Error extracting PDF with PyPDF2: {e}")
            raise
    
    def _extract_text_file(self, file_path: str) -> tuple[str, DocumentMetadata]:
        """Extract text from markdown or text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            metadata = DocumentMetadata(
                filename=filename,
                file_type=file_ext[1:],  # Remove the dot
                page_count=1,
                total_chars=len(content),
                total_words=len(content.split())
            )
            
            # For markdown files, try to extract title from first header
            if file_ext == '.md':
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    metadata.title = title_match.group(1).strip()
            
            return content, metadata
            
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            raise
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean up extracted text while preserving important structure"""
        if not text:
            return ""
        
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove lines with only whitespace
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove excessive spaces but preserve intentional spacing
        text = re.sub(r' {3,}', '  ', text)
        
        # Clean up common PDF extraction artifacts
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between joined words
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)      # Fix hyphenated words split across lines
        
        return text.strip()
    
    def get_document_stats(self, text: str, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Get detailed statistics about the document"""
        lines = text.split('\n')
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        
        # Estimate sentences (simple approach)
        sentences = len(re.findall(r'[.!?]+', text))
        
        stats = {
            'filename': metadata.filename,
            'file_type': metadata.file_type,
            'pages': metadata.page_count or 1,
            'characters': len(text),
            'words': len(text.split()),
            'lines': len(lines),
            'paragraphs': len(paragraphs),
            'sentences': sentences,
            'avg_words_per_sentence': len(text.split()) / max(sentences, 1),
            'avg_chars_per_word': len(text) / max(len(text.split()), 1)
        }
        
        if metadata.title:
            stats['title'] = metadata.title
        if metadata.author:
            stats['author'] = metadata.author
            
        return stats

# Utility functions
def get_supported_file_types() -> List[str]:
    """Get list of supported file extensions"""
    return ['.pdf', '.md', '.txt']

def is_supported_file(file_path: str) -> bool:
    """Check if file type is supported"""
    _, ext = os.path.splitext(file_path.lower())
    return ext in get_supported_file_types()

def get_processor_info() -> Dict[str, str]:
    """Get information about available processors"""
    return {
        'pdf_processor': PDF_PROCESSOR,
        'supported_types': ', '.join(get_supported_file_types())
    }
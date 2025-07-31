"""
Advanced Chunking Strategies for Knowledge Base Documents
Provides multiple chunking approaches for different document types and use cases
"""

import re
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter
)
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk"""
    source_file: str
    chunk_index: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    document_type: str = "unknown"
    char_count: int = 0
    word_count: int = 0
    sentences: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number or 0,
            "section_title": self.section_title or "",
            "document_type": self.document_type,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "sentences": self.sentences
        }

@dataclass
class DocumentChunk:
    """A chunk of text with metadata"""
    content: str
    metadata: ChunkMetadata
    
    def __post_init__(self):
        """Calculate stats after initialization"""
        self.metadata.char_count = len(self.content)
        self.metadata.word_count = len(word_tokenize(self.content))
        self.metadata.sentences = len(sent_tokenize(self.content))

class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies"""
    
    @abstractmethod
    def chunk_text(self, text: str, source_file: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text into smaller pieces with metadata"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this chunking strategy"""
        pass

class RecursiveChunkingStrategy(ChunkingStrategy):
    """Enhanced recursive character text splitting with better defaults"""
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200, 
                 separators: Optional[List[str]] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len
        )
    
    def chunk_text(self, text: str, source_file: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text using recursive character splitting"""
        chunks = self.splitter.split_text(text)
        document_chunks = []
        
        for i, chunk_text in enumerate(chunks):
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=i,
                document_type=kwargs.get('document_type', 'unknown')
            )
            document_chunks.append(DocumentChunk(chunk_text, metadata))
        
        return document_chunks
    
    def get_strategy_name(self) -> str:
        return "recursive_character"

class SemanticChunkingStrategy(ChunkingStrategy):
    """Semantic chunking that respects sentence and paragraph boundaries"""
    
    def __init__(self, target_chunk_size: int = 1200, max_chunk_size: int = 1500):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_text(self, text: str, source_file: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text semantically by paragraphs and sentences"""
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed max size, finish current chunk
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            # If this paragraph alone is too big, split by sentences
            elif len(paragraph) > self.max_chunk_size:
                # Finish current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Split long paragraph by sentences
                sentences = sent_tokenize(paragraph)
                sentence_chunk = ""
                
                for sentence in sentences:
                    if len(sentence_chunk) + len(sentence) > self.max_chunk_size and sentence_chunk:
                        chunks.append(sentence_chunk.strip())
                        sentence_chunk = sentence
                    else:
                        sentence_chunk += " " + sentence if sentence_chunk else sentence
                
                if sentence_chunk:
                    current_chunk = sentence_chunk
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Convert to DocumentChunk objects with metadata
        document_chunks = []
        for i, chunk_text in enumerate(chunks):
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=i,
                document_type=kwargs.get('document_type', 'unknown')
            )
            document_chunks.append(DocumentChunk(chunk_text, metadata))
        
        return document_chunks
    
    def get_strategy_name(self) -> str:
        return "semantic_paragraph"

class MarkdownAwareChunkingStrategy(ChunkingStrategy):
    """Markdown-aware chunking that preserves headers and structure"""
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Define headers to split on
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"), 
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def chunk_text(self, text: str, source_file: str, **kwargs) -> List[DocumentChunk]:
        """Chunk markdown text preserving header structure"""
        # First split by headers
        header_splits = self.markdown_splitter.split_text(text)
        
        # Then split each section if needed
        all_chunks = []
        for header_split in header_splits:
            content = header_split.page_content
            metadata_dict = header_split.metadata
            
            # If content is small enough, keep as one chunk
            if len(content) <= self.chunk_size:
                all_chunks.append((content, metadata_dict))
            else:
                # Split large sections further
                sub_chunks = self.text_splitter.split_text(content)
                for sub_chunk in sub_chunks:
                    all_chunks.append((sub_chunk, metadata_dict))
        
        # Convert to DocumentChunk objects
        document_chunks = []
        for i, (chunk_text, md_metadata) in enumerate(all_chunks):
            section_title = None
            for key, value in md_metadata.items():
                if key.startswith("Header"):
                    section_title = value
                    break
            
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=i,
                section_title=section_title,
                document_type="markdown"
            )
            document_chunks.append(DocumentChunk(chunk_text, metadata))
        
        return document_chunks
    
    def get_strategy_name(self) -> str:
        return "markdown_aware"

class SlidingWindowChunkingStrategy(ChunkingStrategy):
    """Sliding window chunking with configurable overlap"""
    
    def __init__(self, chunk_size: int = 1200, overlap_size: int = 300):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
    
    def chunk_text(self, text: str, source_file: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text using sliding window approach"""
        if len(text) <= self.chunk_size:
            # Text fits in one chunk
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=0,
                document_type=kwargs.get('document_type', 'unknown')
            )
            return [DocumentChunk(text, metadata)]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            # Try to end at a sentence boundary if possible
            if end < len(text):
                # Look for sentence ending within last 100 characters
                last_part = chunk_text[-100:]
                sentence_ends = [m.end() for m in re.finditer(r'[.!?]\s+', last_part)]
                if sentence_ends:
                    # Use the last sentence ending
                    adjustment = sentence_ends[-1] - len(last_part)
                    end = start + self.chunk_size + adjustment
                    chunk_text = text[start:end]
            
            metadata = ChunkMetadata(
                source_file=source_file,
                chunk_index=chunk_index,
                document_type=kwargs.get('document_type', 'unknown')
            )
            chunks.append(DocumentChunk(chunk_text, metadata))
            
            # Move start position (with overlap)
            start = end - self.overlap_size
            chunk_index += 1
            
            # Prevent infinite loop
            if start >= end:
                break
        
        return chunks
    
    def get_strategy_name(self) -> str:
        return "sliding_window"

class ChunkingStrategyFactory:
    """Factory for creating chunking strategies"""
    
    _strategies = {
        'recursive': RecursiveChunkingStrategy,
        'semantic': SemanticChunkingStrategy,
        'markdown': MarkdownAwareChunkingStrategy,
        'sliding_window': SlidingWindowChunkingStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str, **kwargs) -> ChunkingStrategy:
        """Create a chunking strategy by name"""
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(cls._strategies.keys())}")
        
        return cls._strategies[strategy_name](**kwargs)
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """Get list of available strategy names"""
        return list(cls._strategies.keys())
    
    @classmethod
    def get_recommended_strategy(cls, file_path: str) -> str:
        """Get recommended strategy based on file type"""
        if file_path.endswith('.md'):
            return 'markdown'
        elif file_path.endswith('.pdf'):
            return 'semantic'
        else:
            return 'recursive'

# Configuration helper
class ChunkingConfig:
    """Configuration for chunking strategies"""
    
    DEFAULT_CONFIG = {
        'recursive': {
            'chunk_size': 1200,
            'chunk_overlap': 200
        },
        'semantic': {
            'target_chunk_size': 1200,
            'max_chunk_size': 1500
        },
        'markdown': {
            'chunk_size': 1200,
            'chunk_overlap': 200
        },
        'sliding_window': {
            'chunk_size': 1200,
            'overlap_size': 300
        }
    }
    
    @classmethod
    def get_config(cls, strategy_name: str) -> Dict[str, Any]:
        """Get configuration for a strategy"""
        return cls.DEFAULT_CONFIG.get(strategy_name, {})
    
    @classmethod
    def create_configured_strategy(cls, strategy_name: str, custom_config: Optional[Dict[str, Any]] = None) -> ChunkingStrategy:
        """Create a strategy with configuration"""
        config = cls.get_config(strategy_name)
        if custom_config:
            config.update(custom_config)
        
        return ChunkingStrategyFactory.create_strategy(strategy_name, **config)
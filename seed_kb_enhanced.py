#!/usr/bin/env python3
"""
Enhanced Knowledge Base Seeder
Processes documents using advanced chunking strategies and better extraction
"""

import os
import json
import argparse
import logging
from typing import List, Optional
from langchain_community.embeddings import OpenAIEmbeddings
from redis import Redis
from dotenv import load_dotenv

# Import our enhanced modules
from document_processor import EnhancedDocumentProcessor, get_processor_info, is_supported_file
from chunking_strategies import ChunkingStrategyFactory, ChunkingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class EnhancedKnowledgeBaseSeeder:
    """Enhanced knowledge base seeder with multiple chunking strategies"""
    
    def __init__(self, redis_client: Redis, openai_api_key: str, embedding_model: str = "text-embedding-ada-002"):
        self.client = redis_client
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openai_api_key)
        self.document_processor = EnhancedDocumentProcessor(preserve_formatting=True)
        
        logger.info(f"Initialized KnowledgeBaseSeeder with {embedding_model}")
        logger.info(f"Document processor info: {get_processor_info()}")
    
    def process_document(self, file_path: str, chunking_strategy: str = "auto", 
                        key_prefix: str = "agent:kb:doc", custom_config: Optional[dict] = None) -> int:
        """Process a single document with specified chunking strategy"""
        try:
            if not is_supported_file(file_path):
                logger.warning(f"Unsupported file type: {file_path}")
                return 0
            
            logger.info(f"Processing document: {file_path}")
            
            # Extract text and metadata
            text, doc_metadata = self.document_processor.extract_text_and_metadata(file_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return 0
            
            # Get document stats
            doc_stats = self.document_processor.get_document_stats(text, doc_metadata)
            logger.info(f"Document stats: {doc_stats['words']} words, {doc_stats['characters']} chars, {doc_stats['pages']} pages")
            
            # Determine chunking strategy
            if chunking_strategy == "auto":
                chunking_strategy = ChunkingStrategyFactory.get_recommended_strategy(file_path)
            
            logger.info(f"Using chunking strategy: {chunking_strategy}")
            
            # Create chunking strategy
            strategy = ChunkingConfig.create_configured_strategy(chunking_strategy, custom_config)
            
            # Chunk the document
            document_chunks = strategy.chunk_text(
                text, 
                source_file=os.path.basename(file_path),
                document_type=doc_metadata.file_type
            )
            
            logger.info(f"Created {len(document_chunks)} chunks")
            
            # Process and store chunks
            chunks_stored = 0
            for chunk in document_chunks:
                try:
                    # Generate embedding
                    vector = self.embeddings.embed_query(chunk.content)
                    
                    # Create unique key for this chunk
                    chunk_key = f"{key_prefix}:{hash(chunk.content)}"
                    
                    # Prepare chunk data with metadata
                    chunk_data = {
                        "content": chunk.content,
                        "vector": json.dumps(vector),
                        "source_file": chunk.metadata.source_file,
                        "chunk_index": chunk.metadata.chunk_index,
                        "document_type": chunk.metadata.document_type,
                        "char_count": chunk.metadata.char_count,
                        "word_count": chunk.metadata.word_count,
                        "sentences": chunk.metadata.sentences,
                        "chunking_strategy": chunking_strategy
                    }
                    
                    # Add optional metadata
                    if chunk.metadata.page_number:
                        chunk_data["page_number"] = chunk.metadata.page_number
                    if chunk.metadata.section_title:
                        chunk_data["section_title"] = chunk.metadata.section_title
                    if doc_metadata.title:
                        chunk_data["document_title"] = doc_metadata.title
                    if doc_metadata.author:
                        chunk_data["document_author"] = doc_metadata.author
                    
                    # Store in Redis
                    self.client.hset(chunk_key, mapping=chunk_data)
                    chunks_stored += 1
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk.metadata.chunk_index}: {e}")
                    continue
            
            logger.info(f"Successfully stored {chunks_stored}/{len(document_chunks)} chunks from {file_path}")
            return chunks_stored
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def process_directory(self, directory_path: str, chunking_strategy: str = "auto", 
                         key_prefix: str = "agent:kb:doc", custom_config: Optional[dict] = None) -> dict:
        """Process all supported documents in a directory"""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all supported files
        file_paths = []
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path) and is_supported_file(file_path):
                file_paths.append(file_path)
        
        if not file_paths:
            logger.warning(f"No supported files found in {directory_path}")
            return {"processed": 0, "failed": 0, "total_chunks": 0}
        
        logger.info(f"Found {len(file_paths)} supported files to process")
        
        # Process each file
        results = {
            "processed": 0,
            "failed": 0,
            "total_chunks": 0,
            "file_results": {}
        }
        
        for file_path in file_paths:
            try:
                chunks_stored = self.process_document(file_path, chunking_strategy, key_prefix, custom_config)
                results["processed"] += 1
                results["total_chunks"] += chunks_stored
                results["file_results"][os.path.basename(file_path)] = {
                    "status": "success",
                    "chunks": chunks_stored
                }
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results["failed"] += 1
                results["file_results"][os.path.basename(file_path)] = {
                    "status": "failed",
                    "error": str(e)
                }
                continue
        
        logger.info(f"Processing complete: {results['processed']} successful, {results['failed']} failed, {results['total_chunks']} total chunks")
        return results
    
    def get_chunking_strategies(self) -> List[str]:
        """Get available chunking strategies"""
        return ChunkingStrategyFactory.get_available_strategies()
    
    def clear_knowledge_base(self, key_prefix: str = "agent:kb:doc") -> int:
        """Clear all knowledge base entries"""
        pattern = f"{key_prefix}:*"
        keys = self.client.keys(pattern)
        if keys:
            deleted = self.client.delete(*keys)
            logger.info(f"Cleared {deleted} knowledge base entries")
            return deleted
        return 0

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Enhanced Knowledge Base Seeder")
    parser.add_argument("path", help="File or directory path to process")
    parser.add_argument("--strategy", "-s", default="auto", 
                       help="Chunking strategy (auto, recursive, semantic, markdown, sliding_window)")
    parser.add_argument("--key-prefix", default="agent:kb:doc", 
                       help="Redis key prefix for chunks")
    parser.add_argument("--chunk-size", type=int, help="Custom chunk size")
    parser.add_argument("--chunk-overlap", type=int, help="Custom chunk overlap")
    parser.add_argument("--clear", action="store_true", help="Clear existing knowledge base first")
    parser.add_argument("--list-strategies", action="store_true", 
                       help="List available chunking strategies")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize components
    try:
        client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD"),
            decode_responses=True
        )
        client.ping()
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            return 1
        
        seeder = EnhancedKnowledgeBaseSeeder(client, openai_api_key)
        
        # List strategies if requested
        if args.list_strategies:
            strategies = seeder.get_chunking_strategies()
            print("Available chunking strategies:")
            for strategy in strategies:
                config = ChunkingConfig.get_config(strategy)
                print(f"  - {strategy}: {config}")
            return 0
        
        # Clear existing knowledge base if requested
        if args.clear:
            deleted = seeder.clear_knowledge_base(args.key_prefix)
            logger.info(f"Cleared {deleted} existing entries")
        
        # Prepare custom configuration
        custom_config = {}
        if args.chunk_size:
            custom_config["chunk_size"] = args.chunk_size
        if args.chunk_overlap:
            custom_config["chunk_overlap"] = args.chunk_overlap
        
        # Process path
        if os.path.isfile(args.path):
            chunks_stored = seeder.process_document(
                args.path, args.strategy, args.key_prefix, custom_config
            )
            print(f"Successfully processed file: {chunks_stored} chunks stored")
        elif os.path.isdir(args.path):
            results = seeder.process_directory(
                args.path, args.strategy, args.key_prefix, custom_config
            )
            print(f"Directory processing complete:")
            print(f"  Files processed: {results['processed']}")
            print(f"  Files failed: {results['failed']}")
            print(f"  Total chunks: {results['total_chunks']}")
        else:
            logger.error(f"Path not found: {args.path}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
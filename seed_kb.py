#!/usr/bin/env python3
"""
Knowledge Base Seeder - Backward Compatible Wrapper
Uses enhanced processing with improved defaults
"""

import os
import sys
from redis import Redis
from dotenv import load_dotenv

# Try to use enhanced seeder, fallback to original if dependencies missing
try:
    from seed_kb_enhanced import EnhancedKnowledgeBaseSeeder
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    # Fallback imports for original functionality
    import json
    import PyPDF2
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.embeddings import OpenAIEmbeddings

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KB_DATA_PATH = os.getenv("KB_DATA_PATH", "./kb_seed_data")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "auto")

# Redis client
client = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)
client.ping()

def main():
    """Main function with enhanced or fallback processing"""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    if not os.path.exists(KB_DATA_PATH):
        print(f"Error: KB_DATA_PATH directory not found: {KB_DATA_PATH}")
        sys.exit(1)
    
    print(f"Processing knowledge base from: {KB_DATA_PATH}")
    print(f"Using embedding model: {EMBEDDING_MODEL}")
    
    if ENHANCED_AVAILABLE:
        print("Using enhanced processing with advanced chunking strategies")
        try:
            # Use enhanced seeder
            seeder = EnhancedKnowledgeBaseSeeder(client, OPENAI_API_KEY, EMBEDDING_MODEL)
            
            # Process directory with enhanced features
            results = seeder.process_directory(
                KB_DATA_PATH, 
                chunking_strategy=CHUNKING_STRATEGY,
                key_prefix="agent:kb:doc"
            )
            
            print(f"\nProcessing Results:")
            print(f"  Files processed: {results['processed']}")
            print(f"  Files failed: {results['failed']}")
            print(f"  Total chunks created: {results['total_chunks']}")
            
            if results['file_results']:
                print(f"\nFile Details:")
                for filename, result in results['file_results'].items():
                    if result['status'] == 'success':
                        print(f"  ✓ {filename}: {result['chunks']} chunks")
                    else:
                        print(f"  ✗ {filename}: {result['error']}")
            
        except Exception as e:
            print(f"Enhanced processing failed: {e}")
            print("Falling back to basic processing...")
            ENHANCED_AVAILABLE = False
    
    if not ENHANCED_AVAILABLE:
        print("Using basic processing (legacy mode)")
        # Fallback to original processing
        def extract_text(file_path):
            try:
                if file_path.endswith('.md'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                elif file_path.endswith('.pdf'):
                    text = ""
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            text += page.extract_text() or ""
                    return text
                else:
                    raise ValueError(f"Unsupported file type: {file_path}")
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                raise

        def seed_kb_basic(file_path, model_name, key_prefix):
            try:
                text = extract_text(file_path)
                splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)  # Improved defaults
                embeddings = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)
                chunks = splitter.split_text(text)
                
                for i, chunk in enumerate(chunks):
                    client.hset(f"{key_prefix}:{hash(chunk)}", mapping={
                        "content": chunk,
                        "vector": json.dumps(embeddings.embed_query(chunk)),
                        "source_file": os.path.basename(file_path),
                        "chunk_index": i,
                        "chunking_strategy": "recursive_basic"
                    })
                
                print(f"Successfully processed {file_path} - {len(chunks)} chunks")
                return len(chunks)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                raise

        # Process files
        file_paths = [
            os.path.join(KB_DATA_PATH, f) 
            for f in os.listdir(KB_DATA_PATH) 
            if f.endswith(".md") or f.endswith(".pdf")
        ]
        
        if not file_paths:
            print(f"No supported files found in {KB_DATA_PATH}")
            sys.exit(1)
        
        processed = 0
        failed = 0
        total_chunks = 0
        
        for file_path in file_paths:
            try:
                chunks = seed_kb_basic(file_path, EMBEDDING_MODEL, "agent:kb:doc")
                processed += 1
                total_chunks += chunks
            except Exception as e:
                print(f"Failed to process {file_path}, continuing with next file...")
                failed += 1
                continue
        
        print(f"\nBasic Processing Complete:")
        print(f"  Files processed: {processed}")
        print(f"  Files failed: {failed}")
        print(f"  Total chunks: {total_chunks}")

if __name__ == "__main__":
    main()


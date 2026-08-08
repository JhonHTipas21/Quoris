import os
from pathlib import Path
from src.config import DOCS_DIR
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore

def index_all_documents():
    print("--- Starting Document Ingestion Pipeline ---")
    
    # 1. Initialize components
    parser = MarkdownParser()
    chunker = SemanticCodeChunker(target_size=600, overlap_size=100)
    
    print("Loading local embedding model (SentenceTransformers: all-MiniLM-L6-v2)...")
    embedder = LocalEmbedder()
    
    print("Initializing Chroma Vector Store...")
    vector_store = ChromaVectorStore(embedder=embedder)
    
    # 2. Find all markdown files in docs/
    md_files = list(DOCS_DIR.glob("**/*.md"))
    if not md_files:
        print(f"No markdown documents found in {DOCS_DIR}. Please add some first.")
        return
        
    print(f"Found {len(md_files)} documentation files to process.")
    
    total_chunks_processed = 0
    
    # 3. Process each document
    for file_path in md_files:
        print(f"Processing: {file_path.relative_to(DOCS_DIR.parent)}")
        
        try:
            # Parse document by headers
            parsed_docs = parser.load(str(file_path))
            # Split sections into semantic chunks (preserving code blocks)
            chunks = chunker.chunk(parsed_docs)
            
            print(f"  - Parsed {len(parsed_docs)} header sections")
            print(f"  - Generated {len(chunks)} context-aware chunks")
            
            # Ingest chunks into Chroma (content hashing will automatically skip unchanged chunks)
            vector_store.add_documents(chunks)
            total_chunks_processed += len(chunks)
            
        except Exception as e:
            print(f"  [ERROR] Failed to process {file_path}: {e}")
            
    print(f"\n--- Ingestion Completed. Processed {total_chunks_processed} chunks in total. ---")

if __name__ == "__main__":
    index_all_documents()

import argparse
import sys
from src.config import DOCS_DIR
from src.logger import get_logger
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore
from src.retriever import LocalBM25Retriever

logger = get_logger("quoris_cli")

def get_db():
    embedder = LocalEmbedder()
    return ChromaVectorStore(embedder=embedder)

def run_status(args):
    """Display vector store collection details and count."""
    try:
        vs = get_db()
        count = vs.collection.count()
        logger.info(f"Connected to Chroma collection: '{vs.collection.name}'")
        logger.info(f"Total indexed document chunks: {count}")
        print(f"Collection Name: {vs.collection.name}")
        print(f"Total Chunks: {count}")
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        sys.exit(1)

def run_wipe(args):
    """Wipe the entire collection from the vector store."""
    try:
        vs = get_db()
        count = vs.collection.count()
        logger.warning(f"Wiping collection '{vs.collection.name}' containing {count} chunks...")
        
        # Chroma client allows deleting collections or deleting by ids
        # Deleting all matching IDs is safer:
        if count > 0:
            all_docs = vs.collection.get()
            if all_docs and "ids" in all_docs:
                vs.collection.delete(ids=all_docs["ids"])
                
        logger.info("Collection successfully wiped.")
        print("Vector database collection successfully wiped.")
    except Exception as e:
        logger.error(f"Failed to wipe database: {e}")
        sys.exit(1)

def run_index(args):
    """Execute the full documents ingestion pipeline."""
    from src.index_docs import index_all_documents
    try:
        index_all_documents()
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)

def run_query(args):
    """Perform a direct semantic query against vector database."""
    try:
        vs = get_db()
        embedder = vs.embedder
        
        print(f"Executing semantic search for: '{args.text}' (k={args.k})")
        vector = embedder.embed_query(args.text)
        results = vs.search(query_vector=vector, k=args.k)
        
        print(f"\nFound {len(results)} matching chunks:\n")
        for idx, doc in enumerate(results, start=1):
            provider = doc.metadata.get("api_provider", "N/A")
            path = doc.metadata.get("header_path", "N/A")
            url = doc.metadata.get("source_url", "N/A")
            
            print(f"[{idx}] Provider: {provider.upper()} | Path: {path}")
            print(f"    Source URL: {url}")
            print(f"    Content Snippet: {doc.page_content[:150]}...")
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Quoris Command Line Interface - Manage Chroma DB and ingestions"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Status Command
    subparsers.add_parser("status", help="Show vector database collection status and item counts")

    # Wipe Command
    subparsers.add_parser("wipe", help="Clear all indexed document chunks from the collection")

    # Index Command
    subparsers.add_parser("index", help="Run the parser and ingestion pipeline to update the database")

    # Query Command
    query_parser = subparsers.add_parser("query", help="Execute semantic query directly on vector store")
    query_parser.add_argument("--text", type=str, required=True, help="Query text to search")
    query_parser.add_argument("-k", type=int, default=3, help="Number of nearest neighbors to retrieve")

    args = parser.parse_args()

    if args.command == "status":
        run_status(args)
    elif args.command == "wipe":
        run_wipe(args)
    elif args.command == "index":
        run_index(args)
    elif args.command == "query":
        run_query(args)

if __name__ == "__main__":
    main()

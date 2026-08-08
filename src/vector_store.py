import chromadb
from typing import List, Dict, Any, Optional
from src.document import Document
from src.interfaces import VectorStore, Embedder
from src.config import DB_DIR

class ChromaVectorStore(VectorStore):
    """
    Local Chroma Vector Store wrapper.
    - Implements incremental updates via content hashing.
    - Supports metadata filtering (e.g. filtering by api_provider).
    - Decoupled from embedding generation (receives Embedder in constructor).
    """
    
    def __init__(self, embedder: Embedder, collection_name: str = "payment_docs"):
        self.embedder = embedder
        # Setup persistent client
        self.client = chromadb.PersistentClient(path=str(DB_DIR))
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # cosine similarity is standard for text
        )

    def _generate_doc_id(self, doc: Document) -> str:
        """Generate a deterministic and unique ID for a chunk."""
        provider = doc.metadata.get("api_provider", "generic")
        source = doc.metadata.get("source_file", "unknown")
        idx = doc.metadata.get("chunk_index", 0)
        # Sanitize ID to avoid invalid characters in Chroma
        sanitized_source = source.replace(".", "_").replace("/", "_")
        return f"{provider}_{sanitized_source}_chunk_{idx}"

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        ids_to_add: List[str] = []
        texts_to_add: List[str] = []
        metadatas_to_add: List[Dict[str, Any]] = []

        # Fetch existing document IDs and hashes to check for updates
        doc_ids = [self._generate_doc_id(doc) for doc in documents]
        
        existing = self.collection.get(
            ids=doc_ids,
            include=["metadatas"]
        )
        
        # Build mapping of existing doc_id -> content_hash
        existing_hashes = {}
        if existing and "ids" in existing:
            for idx, doc_id in enumerate(existing["ids"]):
                meta = existing["metadatas"][idx]
                if meta and "content_hash" in meta:
                    existing_hashes[doc_id] = meta["content_hash"]

        for doc, doc_id in zip(documents, doc_ids):
            # Ensure the document's content hash is computed
            doc.update_hash()
            
            # Check if document already exists and has the same hash
            if doc_id in existing_hashes and existing_hashes[doc_id] == doc.content_hash:
                # Content has not changed, skip indexing
                continue
            
            ids_to_add.append(doc_id)
            texts_to_add.append(doc.page_content)
            
            # Build metadata, including the content hash
            meta = doc.metadata.copy()
            meta["content_hash"] = doc.content_hash
            metadatas_to_add.append(meta)

        if ids_to_add:
            # Generate embeddings for new/changed documents
            embeddings = self.embedder.embed_documents(texts_to_add)
            
            # Upsert into Chroma (updates if key exists, inserts otherwise)
            self.collection.upsert(
                ids=ids_to_add,
                embeddings=embeddings,
                documents=texts_to_add,
                metadatas=metadatas_to_add
            )

    def search(self, query_vector: List[float], k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        # Format the filter for Chroma metadata query
        # Chroma format: where={"api_provider": "wompi"}
        where_clause = None
        if metadata_filter:
            # If multiple filters, chroma supports operators, but for simple exact match:
            # where={"api_provider": "wompi"}
            where_clause = metadata_filter

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=where_clause
        )

        documents: List[Document] = []
        
        if results and results.get("documents"):
            ids = results["ids"][0]
            texts = results["documents"][0]
            metadatas = results["metadatas"][0]
            
            for idx, text in enumerate(texts):
                meta = metadatas[idx] or {}
                # Extract content hash from metadata if exists
                content_hash = meta.pop("content_hash", None)
                
                doc = Document(
                    page_content=text,
                    metadata=meta,
                    content_hash=content_hash
                )
                documents.append(doc)
                
        return documents

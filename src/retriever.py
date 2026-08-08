import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from src.document import Document
from src.interfaces import KeywordRetriever, VectorStore, Embedder

class LocalBM25Retriever(KeywordRetriever):
    """
    BM25 Keyword Retriever.
    - Tokenizes corpus for exact matching.
    - Supports metadata pre-filtering to scope search by payment provider.
    """
    
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []

    def _tokenize(self, text: str) -> List[str]:
        # Basic alphanumeric tokenization in lowercase
        return re.findall(r"\b\w+\b", text.lower())

    def index_documents(self, documents: List[Document]) -> None:
        self.documents = documents
        if not documents:
            self.bm25 = None
            return
            
        tokenized_corpus = [self._tokenize(doc.page_content) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query: str, k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        if not self.bm25 or not self.documents:
            return []

        # 1. Apply metadata filter first (pre-filtering)
        filtered_docs_with_indices = []
        for idx, doc in enumerate(self.documents):
            match = True
            if metadata_filter:
                for key, val in metadata_filter.items():
                    if doc.metadata.get(key) != val:
                        match = False
                        break
            if match:
                filtered_docs_with_indices.append((idx, doc))

        if not filtered_docs_with_indices:
            return []

        # 2. Tokenize the search query
        tokenized_query = self._tokenize(query)
        
        # 3. Retrieve BM25 scores for the entire corpus
        all_scores = self.bm25.get_scores(tokenized_query)
        
        # 4. Filter scores using the metadata-matched indices
        scored_docs = []
        for original_idx, doc in filtered_docs_with_indices:
            score = all_scores[original_idx]
            scored_docs.append((doc, score))
            
        # 5. Filter out documents with score <= 0 (no keyword overlap)
        scored_docs = [(doc, score) for doc, score in scored_docs if score > 0]
            
        # 6. Sort documents by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return [doc for doc, score in scored_docs[:k]]


class HybridRetriever:
    """
    Combines Vector search (Dense) and BM25 search (Sparse) using Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(self, vector_store: VectorStore, embedder: Embedder, bm25_retriever: KeywordRetriever):
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25_retriever = bm25_retriever

    def retrieve(self, query: str, k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None, rrf_constant: int = 60) -> List[Document]:
        # 1. Dense retrieval (Vector Search)
        query_vector = self.embedder.embed_query(query)
        vector_results = self.vector_store.search(
            query_vector=query_vector, 
            k=k * 2, # fetch a wider set for fusion
            metadata_filter=metadata_filter
        )
        
        # 2. Sparse retrieval (BM25 Search)
        bm25_results = self.bm25_retriever.search(
            query=query, 
            k=k * 2, 
            metadata_filter=metadata_filter
        )
        
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        content_to_doc: Dict[str, Document] = {}

        # Add Dense ranks
        for rank, doc in enumerate(vector_results):
            doc_key = doc.page_content
            content_to_doc[doc_key] = doc
            rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (rrf_constant + rank + 1))

        # Add Sparse ranks
        for rank, doc in enumerate(bm25_results):
            doc_key = doc.page_content
            content_to_doc[doc_key] = doc
            rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (rrf_constant + rank + 1))

        # Sort documents by RRF score descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Reconstruct Document objects
        fused_docs = [content_to_doc[key] for key in sorted_keys]
        
        return fused_docs[:k]

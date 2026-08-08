from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.document import Document

class DocumentLoader(ABC):
    @abstractmethod
    def load(self, file_path: str) -> List[Document]:
        """Load and parse file into structured Document objects."""
        pass

class Chunker(ABC):
    @abstractmethod
    def chunk(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller, context-aware chunks."""
        pass

class Embedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        pass

class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add or update documents in the vector database."""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Retrieve top k documents matching the query vector."""
        pass

class KeywordRetriever(ABC):
    @abstractmethod
    def index_documents(self, documents: List[Document]) -> None:
        """Index documents for lexical (BM25) search."""
        pass

    @abstractmethod
    def search(self, query: str, k: int = 10, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Retrieve top k documents using BM25 keyword matching."""
        pass

class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, documents: List[Document], top_n: int = 3) -> List[Document]:
        """Re-rank candidate documents based on semantic relevance to the query."""
        pass

class LLMGenerator(ABC):
    @abstractmethod
    def generate(self, query: str, context: List[Document]) -> Dict[str, Any]:
        """Generate response based on query and retrieved context."""
        pass

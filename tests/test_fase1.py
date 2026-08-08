import pytest
from src.document import Document
from src.retriever import LocalBM25Retriever, HybridRetriever
from src.reranker import LocalCrossEncoderReranker
from src.orchestrator import RAGOrchestrator

# Mock Embedder for testing
class MockEmbedder:
    def embed_documents(self, texts):
        return [[0.1] * 384 for _ in texts]
    def embed_query(self, text):
        return [0.1] * 384

# Mock VectorStore for testing
class MockVectorStore:
    def __init__(self):
        self.docs = []
    def add_documents(self, documents):
        self.docs.extend(documents)
    def search(self, query_vector, k=10, metadata_filter=None):
        # Return all documents that match metadata filter
        filtered = []
        for doc in self.docs:
            if metadata_filter:
                match = True
                for key, val in metadata_filter.items():
                    if doc.metadata.get(key) != val:
                        match = False
                        break
                if match:
                    filtered.append(doc)
            else:
                filtered.append(doc)
        return filtered[:k]

# Mock LLM for testing
class MockLLM:
    def generate(self, query, context):
        # Simulate LLM referencing the first document
        return {
            "answer": "La firma de integridad se calcula con SHA256 [Doc 1].",
            "citations": [
                {
                    "id": "[Doc 1]",
                    "api_provider": context[0].metadata.get("api_provider"),
                    "section": context[0].metadata.get("section"),
                    "source_url": context[0].metadata.get("source_url")
                }
            ]
        }

@pytest.fixture
def mock_documents():
    return [
        Document(
            page_content="Para generar la firma de integridad de Wompi, debes usar SHA256 concatenando referencia, monto y secreto.",
            metadata={"api_provider": "wompi", "source_file": "signatures.md", "section": "Generación de la firma", "source_url": "https://docs.wompi.co/signatures", "header_path": "Wompi > Firmas > Generacion"}
        ),
        Document(
            page_content="El token de aceptación es obligatorio en Wompi para cumplir Habeas Data.",
            metadata={"api_provider": "wompi", "source_file": "acceptance.md", "section": "Tokens de aceptación", "source_url": "https://docs.wompi.co/acceptance", "header_path": "Wompi > Aceptacion"}
        ),
        Document(
            page_content="Stripe uses API Keys passed in the Authorization Bearer header for direct integrations.",
            metadata={"api_provider": "stripe", "source_file": "auth.md", "section": "API keys", "source_url": "https://docs.stripe.com/auth", "header_path": "Stripe > Authentication"}
        )
    ]

def test_bm25_retriever(mock_documents):
    retriever = LocalBM25Retriever()
    retriever.index_documents(mock_documents)
    
    # Simple search
    results = retriever.search("firma de integridad", k=1)
    assert len(results) == 1
    assert "firma de integridad" in results[0].page_content
    
    # Metadata filter search
    results_filtered = retriever.search("token", k=5, metadata_filter={"api_provider": "stripe"})
    assert len(results_filtered) == 0  # No doc matching 'token' and api_provider 'stripe'
    
    results_filtered_wompi = retriever.search("token", k=5, metadata_filter={"api_provider": "wompi"})
    assert len(results_filtered_wompi) == 1
    assert "Habeas Data" in results_filtered_wompi[0].page_content

def test_hybrid_retriever_rrf(mock_documents):
    vs = MockVectorStore()
    vs.add_documents(mock_documents)
    
    embedder = MockEmbedder()
    bm25 = LocalBM25Retriever()
    bm25.index_documents(mock_documents)
    
    hybrid = HybridRetriever(vector_store=vs, embedder=embedder, bm25_retriever=bm25)
    
    # Test fusion retrieves top docs
    results = hybrid.retrieve("firma de integridad", k=2)
    assert len(results) == 2
    # The most lexical-matching should be ranked first
    assert "firma" in results[0].page_content

def test_orchestrator(mock_documents):
    vs = MockVectorStore()
    vs.add_documents(mock_documents)
    embedder = MockEmbedder()
    bm25 = LocalBM25Retriever()
    bm25.index_documents(mock_documents)
    
    hybrid = HybridRetriever(vector_store=vs, embedder=embedder, bm25_retriever=bm25)
    
    # Mock Reranker to just slice first top_n docs
    class MockReranker:
        def rerank(self, query, documents, top_n=3):
            return documents[:top_n]
            
    llm = MockLLM()
    
    orch = RAGOrchestrator(hybrid_retriever=hybrid, reranker=MockReranker(), llm=llm)
    
    # 1. Query targeting Wompi (should detect metadata filter)
    response = orch.query("¿Cómo calcular la firma en Wompi?")
    
    assert response["metadata_filter_applied"] == {"api_provider": "wompi"}
    assert "SHA256" in response["answer"]
    assert len(response["citations"]) == 1
    assert response["citations"][0]["id"] == "[Doc 1]"
    assert response["citations"][0]["api_provider"] == "wompi"
    assert response["citations"][0]["source_url"] == "https://docs.wompi.co/signatures"
    
    # 2. Query targeting Stripe (should detect stripe metadata filter)
    response_stripe = orch.query("How to authorize Stripe requests?")
    assert response_stripe["metadata_filter_applied"] == {"api_provider": "stripe"}

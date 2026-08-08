import pytest
from unittest.mock import MagicMock, patch
from src.document import Document
from src.retriever import LocalBM25Retriever, HybridRetriever

# =========================================================================
# LocalBM25Retriever Tests
# =========================================================================

def make_doc(content: str, provider: str = "wompi", section: str = "intro") -> Document:
    return Document(
        page_content=content,
        metadata={"api_provider": provider, "header_path": section}
    )

@pytest.fixture
def bm25_retriever():
    retriever = LocalBM25Retriever()
    docs = [
        make_doc("La firma de integridad usa SHA256 y un secreto compartido.", "wompi", "firmas"),
        make_doc("Los webhooks de Wompi notifican el estado de los pagos.", "wompi", "webhooks"),
        make_doc("Stripe requiere un PaymentIntent para cobrar con tarjeta.", "stripe", "intents"),
        make_doc("MercadoPago usa card_token para tokenizar tarjetas de credito.", "mercadopago", "tokens"),
    ]
    retriever.index_documents(docs)
    return retriever

def test_bm25_retriever_indexes_corpus(bm25_retriever):
    assert bm25_retriever.bm25 is not None
    assert len(bm25_retriever.documents) == 4

def test_bm25_search_returns_relevant_results(bm25_retriever):
    results = bm25_retriever.search(query="firma integridad SHA256", k=2)
    assert len(results) > 0
    # The first result should be about signatures (firma)
    top_content = results[0].page_content.lower()
    assert "firma" in top_content or "sha256" in top_content

def test_bm25_search_filters_by_provider(bm25_retriever):
    results = bm25_retriever.search(
        query="tokenizar tarjetas de credito",
        k=4,
        metadata_filter={"api_provider": "mercadopago"}
    )
    for doc in results:
        assert doc.metadata["api_provider"] == "mercadopago"

def test_bm25_search_excludes_zero_score_results(bm25_retriever):
    # A query completely unrelated to the corpus should return no results
    # due to zero-score filtering
    results = bm25_retriever.search(
        query="inteligencia artificial machine learning datasets",
        k=4
    )
    assert len(results) == 0

def test_bm25_search_with_empty_corpus():
    retriever = LocalBM25Retriever()
    retriever.index_documents([])
    results = retriever.search(query="cualquier query", k=3)
    assert results == []

# =========================================================================
# HybridRetriever Tests (using mocks to isolate from Chroma and embedder)
# =========================================================================

def test_hybrid_retriever_rrf_fusion():
    # Mock vector store
    mock_vs = MagicMock()
    mock_vs.search.return_value = [
        make_doc("Vector result A — firma SHA256", "wompi", "firmas"),
        make_doc("Vector result B — webhook notificacion", "wompi", "webhooks"),
    ]

    # Mock embedder
    mock_embedder = MagicMock()
    mock_embedder.embed_query.return_value = [0.1] * 384

    # Mock BM25 retriever
    mock_bm25 = MagicMock()
    mock_bm25.search.return_value = [
        make_doc("Vector result B — webhook notificacion", "wompi", "webhooks"),
        make_doc("BM25 result C — token de aceptacion", "wompi", "intro"),
    ]

    retriever = HybridRetriever(
        vector_store=mock_vs,
        embedder=mock_embedder,
        bm25_retriever=mock_bm25
    )

    results = retriever.retrieve(query="webhook firma wompi", k=3)

    assert len(results) <= 3
    # Result B appears in both vector and BM25, so should be ranked higher via RRF
    result_contents = [doc.page_content for doc in results]
    assert any("webhook" in c for c in result_contents)

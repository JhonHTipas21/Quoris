import time
from typing import List, Dict, Any, Optional
from src.document import Document
from src.interfaces import Reranker, LLMGenerator
from src.retriever import HybridRetriever
from src.rewriter import GroqQueryRewriter
from src.logger import get_logger

class RAGOrchestrator:
    """
    Main Orchestrator for Quoris 7-Layer RAG Pipeline.
    Coordinates: Query Analysis -> Filtering -> Hybrid Search -> Reranking -> LLM Grounding -> Footnote Citations.
    """
    
    def __init__(self, hybrid_retriever: HybridRetriever, reranker: Reranker, llm: LLMGenerator, query_rewriter: Optional[GroqQueryRewriter] = None):
        self.logger = get_logger(__name__)
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker
        self.llm = llm
        self.query_rewriter = query_rewriter

    def _detect_provider_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Analyze the query text to detect payment provider mentions and set up metadata filtering.
        """
        q = query.lower()
        if "wompi" in q:
            return {"api_provider": "wompi"}
        elif "stripe" in q:
            return {"api_provider": "stripe"}
        elif "mercadopago" in q or "mercado pago" in q:
            return {"api_provider": "mercadopago"}
        return None

    def _rewrite_query(self, query: str, provider_filter: Optional[Dict[str, Any]]) -> str:
        """
        Rewrites shorthand or vague user queries into search-optimized terms.
        Applies LLM rewriter if available, combined with rule-based heuristics.
        """
        # 1. Apply LLM query rewriting if enabled
        if self.query_rewriter:
            query = self.query_rewriter.rewrite(query)

        rewritten = query
        # 2. Apply deterministic heuristics for key terminologies
        if provider_filter and provider_filter.get("api_provider") == "wompi":
            if "firma" in query.lower() or "signature" in query.lower():
                rewritten += " firma de integridad sha256 concatenacion secreto"
            if "webhook" in query.lower() or "evento" in query.lower():
                rewritten += " webhook checksum validacion de firma"
            if "aceptacion" in query.lower() or "acceptance" in query.lower():
                rewritten += " token de aceptacion terminos y condiciones"
                
        return rewritten

    def query(self, user_query: str) -> Dict[str, Any]:
        self.logger.info(f"Received user query: '{user_query}'")
        start_time = time.time()
        
        # 1. Analyze and extract metadata filters (e.g. routing by api_provider)
        metadata_filter = self._detect_provider_filter(user_query)
        self.logger.info(f"Metadata filter detected: {metadata_filter}")
        
        # 2. Query Rewriting (expand terminology)
        search_query = self._rewrite_query(user_query, metadata_filter)
        self.logger.info(f"Search query re-written to: '{search_query}'")
        
        # 3. Hybrid Retrieval (Vector + BM25 combined via RRF)
        # Fetch top-10 candidates
        candidates = self.hybrid_retriever.retrieve(
            query=search_query, 
            k=10, 
            metadata_filter=metadata_filter
        )
        self.logger.info(f"Retrieved {len(candidates)} hybrid candidates from vector/lexical retrieval")
        
        # 4. Reranking (Cross-Encoder down to top-3)
        reranked_chunks = self.reranker.rerank(
            query=user_query, 
            documents=candidates, 
            top_n=3
        )
        self.logger.info(f"CrossEncoder reranking completed. Reduced candidates count to {len(reranked_chunks)}")
        
        # 5. LLM Grounded Generation & Citation Extraction
        response_data = self.llm.generate(
            query=user_query, 
            context=reranked_chunks
        )
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Grounded response generated. Citations: {len(response_data['citations'])}. Total Latency: {elapsed_time:.3f}s")
        
        # 6. Build final response payload
        return {
            "query": user_query,
            "search_query": search_query,
            "answer": response_data["answer"],
            "citations": response_data["citations"],
            "context_used": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in reranked_chunks
            ],
            "metadata_filter_applied": metadata_filter,
            "latency_seconds": round(elapsed_time, 3)
        }

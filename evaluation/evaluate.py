import os
import json
import time
from typing import List, Dict, Any
from src.config import GROQ_API_KEY
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore
from src.retriever import LocalBM25Retriever, HybridRetriever
from src.reranker import LocalCrossEncoderReranker
from src.llm import GroqLLMGenerator
from src.orchestrator import RAGOrchestrator

def load_golden_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation():
    print("--- Starting RAG Evaluation ---")
    
    # 1. Initialize RAG system
    parser = MarkdownParser()
    chunker = SemanticCodeChunker()
    embedder = LocalEmbedder()
    vector_store = ChromaVectorStore(embedder=embedder)
    bm25 = LocalBM25Retriever()
    
    # Get all chunks
    from src.config import DOCS_DIR
    md_files = list(DOCS_DIR.glob("**/*.md"))
    all_chunks = []
    for file_path in md_files:
        parsed_docs = parser.load(str(file_path))
        chunks = chunker.chunk(parsed_docs)
        all_chunks.extend(chunks)
        
    bm25.index_documents(all_chunks)
    vector_store.add_documents(all_chunks)
    
    hybrid_retriever = HybridRetriever(vector_store=vector_store, embedder=embedder, bm25_retriever=bm25)
    reranker = LocalCrossEncoderReranker()
    
    has_groq = bool(GROQ_API_KEY)
    if has_groq:
        llm = GroqLLMGenerator(api_key=GROQ_API_KEY)
        orchestrator = RAGOrchestrator(hybrid_retriever=hybrid_retriever, reranker=reranker, llm=llm)
    else:
        print("[INFO] GROQ_API_KEY not found. Running retrieval-only evaluation.")
        orchestrator = None

    golden_data = load_golden_dataset("evaluation/golden_dataset.json")
    print(f"Loaded {len(golden_data)} evaluation cases.")

    total_cases = len(golden_data)
    hits_at_3 = 0
    reciprocal_ranks = []
    latencies = []
    
    evaluation_results = []
    
    for case in golden_data:
        query = case["query"]
        target_section = case["section"]
        
        # Run retrieval step (Hybrid + Reranking)
        start_time = time.time()
        
        # Run orchestrator's filter detection
        meta_filter = {"api_provider": case["provider"]}
        candidates = hybrid_retriever.retrieve(query=query, k=10, metadata_filter=meta_filter)
        retrieved_chunks = reranker.rerank(query=query, documents=candidates, top_n=3)
        
        latency = time.time() - start_time
        latencies.append(latency)
        
        # Calculate Recall and MRR based on matching metadata section
        hit = False
        rr = 0.0
        
        for rank, chunk in enumerate(retrieved_chunks, start=1):
            import re
            import unicodedata
            
            def normalize(t: str) -> str:
                t = t.lower()
                # Remove accents
                t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
                # Keep only alphanumeric
                return re.sub(r'[^a-z0-9]', '', t)
                
            norm_target = normalize(target_section)
            norm_path = normalize(chunk.metadata.get("header_path", ""))
            norm_sec = normalize(chunk.metadata.get("section", ""))
            
            if norm_target in norm_path or norm_target in norm_sec:
                hit = True
                if rr == 0.0:
                    rr = 1.0 / rank
                    
        if hit:
            hits_at_3 += 1
        reciprocal_ranks.append(rr)
        
        # Run LLM response generation if available
        answer = "N/A (Retrieval-Only)"
        citations = []
        if orchestrator:
            try:
                res = orchestrator.query(query)
                answer = res["answer"]
                citations = res["citations"]
            except Exception as e:
                answer = f"Error during query: {e}"

        evaluation_results.append({
            "id": case["id"],
            "query": query,
            "target_section": target_section,
            "retrieved_sections": [c.metadata.get("section") for c in retrieved_chunks],
            "recall_hit": hit,
            "reciprocal_rank": rr,
            "latency_seconds": round(latency, 3),
            "answer": answer,
            "citations_count": len(citations)
        })
        
        print(f"Case {case['id']}: Recall Hit={hit}, MRR={round(rr, 2)}, Latency={round(latency, 2)}s")

    # Calculate final metrics
    recall_at_3 = hits_at_3 / total_cases
    mrr = sum(reciprocal_ranks) / total_cases
    avg_latency = sum(latencies) / total_cases
    
    print("\n--- Evaluation Summary ---")
    print(f"Total Cases: {total_cases}")
    print(f"Recall@3: {recall_at_3 * 100:.2f}%")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.3f}")
    print(f"Average Latency: {avg_latency:.3f}s")
    
    # Save report as a markdown artifact or file
    report_content = f"""# RAG Evaluation Report — Quoris

Generado el: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Métricas Globales
| Métrica | Valor | Objetivo | Estado |
|---|---|---|---|
| **Casos de prueba** | {total_cases} | - | - |
| **Recall@3** | {recall_at_3 * 100:.1f}% | > 85% | {'✅ Aprobado' if recall_at_3 >= 0.85 else '⚠️ Optimizar'} |
| **Mean Reciprocal Rank (MRR)** | {mrr:.3f} | > 0.70 | {'✅ Aprobado' if mrr >= 0.70 else '⚠️ Optimizar'} |
| **Latencia Promedio (Retrieval)** | {avg_latency:.3f}s | < 1.0s | {'✅ Aprobado' if avg_latency < 1.0 else '⚠️ Lento'} |

## Resultados por Caso de Uso
| ID | Pregunta | Sección Objetivo | Recall Hit | MRR | Latencia (s) | Citas |
|---|---|---|---|---|---|---|
"""
    
    for r in evaluation_results:
        report_content += (
            f"| {r['id']} | {r['query']} | {r['target_section']} | "
            f"{'✅' if r['recall_hit'] else '❌'} | {r['reciprocal_rank']:.2f} | "
            f"{r['latency_seconds']}s | {r['citations_count']} |\n"
        )
        
    report_path = "evaluation/evaluation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Evaluation report written to: {report_path}")

if __name__ == "__main__":
    run_evaluation()

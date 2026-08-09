import os
import sys
import json
import argparse
import unicodedata
from typing import List, Dict, Any

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_recall, faithfulness, answer_relevancy
from langchain_groq import ChatGroq
from langchain_core.embeddings import Embeddings

from src.config import GROQ_API_KEY
from src.parser import MarkdownParser
from src.chunker import SemanticCodeChunker
from src.embedder import LocalEmbedder
from src.vector_store import ChromaVectorStore
from src.retriever import LocalBM25Retriever, HybridRetriever
from src.reranker import LocalCrossEncoderReranker
from src.llm import GroqLLMGenerator
from src.orchestrator import RAGOrchestrator
from src.logger import get_logger

logger = get_logger("rag_evaluator")

class LangchainLocalEmbedderWrapper(Embeddings):
    def __init__(self, embedder: LocalEmbedder):
        self.embedder = embedder
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(texts)
    def embed_query(self, text: str) -> List[float]:
        return self.embedder.embed_query(text)

def normalize_text(text: str) -> str:
    text = text.lower()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def run_evaluation(retrieval_only: bool):
    logger.info("Initialize Quoris RAG pipeline...")
    parser = MarkdownParser()
    chunker = SemanticCodeChunker()
    embedder = LocalEmbedder()
    vector_store = ChromaVectorStore(embedder=embedder)
    bm25 = LocalBM25Retriever()
    
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
    
    llm_generator = GroqLLMGenerator(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    orchestrator = RAGOrchestrator(hybrid_retriever=hybrid_retriever, reranker=reranker, llm=llm_generator) if llm_generator else None

    # Determine if Phase 2 can run
    run_phase_2 = not retrieval_only and bool(GROQ_API_KEY)
    if not run_phase_2:
        logger.info("Executing Phase 1 (Retrieval Only). GROQ_API_KEY not found or --retrieval-only specified.")

    dataset_path = "evals/golden_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)
        
    results_dir = "evals/results"
    os.makedirs(results_dir, exist_ok=True)

    # Metrics
    total_cases = len(golden_data)
    hits_at_k = 0
    mrr_sum = 0.0
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    citation_validities = []
    out_of_corpus_passes = 0
    total_out_of_corpus = 0

    logger.info(f"Running evaluation for {total_cases} queries...")

    for item in golden_data:
        query = item["query"]
        expected_keywords = item.get("expected_context_keywords", [])
        is_ooc = (len(expected_keywords) == 0 and "No tengo" in item.get("expected_answer", ""))
        
        # --- PHASE 1: Retrieval ---
        metadata_filter = {"api_provider": item["provider"]} if item.get("provider") != "unknown" else None
        search_query = orchestrator._rewrite_query(query, metadata_filter) if orchestrator else query
        
        candidates = hybrid_retriever.retrieve(query=search_query, k=10, metadata_filter=metadata_filter)
        reranked = reranker.rerank(query=query, documents=candidates, top_n=3)
        
        # Check retrieval hit
        hit = False
        rr = 0.0
        
        if not is_ooc and expected_keywords:
            norm_keywords = [normalize_text(kw) for kw in expected_keywords]
            for rank, doc in enumerate(reranked, start=1):
                norm_content = normalize_text(doc.page_content)
                # Ensure ALL keywords are found in this document for a perfect hit
                if all(kw in norm_content for kw in norm_keywords):
                    hit = True
                    if rr == 0.0:
                        rr = 1.0 / rank
                        
        if hit:
            hits_at_k += 1
        mrr_sum += rr

        # --- PHASE 2: Generation ---
        if run_phase_2:
            if is_ooc:
                total_out_of_corpus += 1
            
            res = orchestrator.query(query)
            ans = res["answer"]
            ctx = [doc.page_content for doc in res["context_used"]]
            citations = res["citations"]
            
            # Citation validity check
            # Any string "[Doc X]" in the answer must have a matching valid citation object
            import re
            doc_refs = re.findall(r'\[Doc (\d+)\]', ans)
            valid_ref_count = 0
            for ref in doc_refs:
                idx = int(ref) - 1
                if 0 <= idx < len(reranked):
                    valid_ref_count += 1
            
            if doc_refs:
                citation_score = valid_ref_count / len(doc_refs)
            else:
                citation_score = 1.0 if not expected_keywords else 0.0 # Expected citations for in-corpus
                
            citation_validities.append(citation_score)
            
            # Out-of-corpus check
            if is_ooc:
                if "no tengo" in ans.lower() or "no tengo informacion" in normalize_text(ans):
                    out_of_corpus_passes += 1
                else:
                    logger.warning(f"OOC Failure: Model hallucinated answer for '{query}': {ans}")

            questions.append(query)
            answers.append(ans)
            contexts.append(ctx)
            ground_truths.append(item["expected_answer"])

    retrieval_recall = hits_at_k / total_cases if total_cases > 0 else 0
    retrieval_mrr = mrr_sum / total_cases if total_cases > 0 else 0
    
    logger.info(f"Retrieval Recall@3: {retrieval_recall:.2f}, MRR: {retrieval_mrr:.2f}")
    
    # Save retrieval results
    current_metrics = {
        "retrieval_recall": retrieval_recall,
        "retrieval_mrr": retrieval_mrr
    }
    
    if run_phase_2:
        # Run RAGAS
        hf_dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        })
        
        judge_llm = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.0)
        judge_embeddings = LangchainLocalEmbedderWrapper(embedder=embedder)
        
        result = evaluate(
            hf_dataset,
            metrics=[context_recall, faithfulness, answer_relevancy],
            llm=judge_llm,
            embeddings=judge_embeddings
        )
        
        metrics_df = result.to_pandas()
        
        avg_context_recall = metrics_df["context_recall"].mean() if "context_recall" in metrics_df else 0.0
        avg_faithfulness = metrics_df["faithfulness"].mean() if "faithfulness" in metrics_df else 0.0
        avg_relevancy = metrics_df["answer_relevancy"].mean() if "answer_relevancy" in metrics_df else 0.0
        avg_citation = sum(citation_validities) / len(citation_validities) if citation_validities else 1.0
        ooc_score = out_of_corpus_passes / total_out_of_corpus if total_out_of_corpus > 0 else 1.0

        current_metrics.update({
            "context_recall": avg_context_recall,
            "faithfulness": avg_faithfulness,
            "answer_relevancy": avg_relevancy,
            "citation_validity": avg_citation,
            "out_of_corpus_safety": ooc_score
        })
    
    with open(os.path.join(results_dir, "generation_metrics.json"), "w") as f:
        json.dump(current_metrics, f)

    # Thresholds
    min_context_recall = float(os.getenv("MIN_CONTEXT_RECALL", "0.75"))
    min_faithfulness = float(os.getenv("MIN_FAITHFULNESS", "0.80"))
    min_relevancy = float(os.getenv("MIN_ANSWER_RELEVANCY", "0.75"))
    min_citation = float(os.getenv("MIN_CITATION_VALIDITY", "0.90"))

    # Check against baseline
    baseline_path = "evals/baseline_metrics.json"
    regression = False
    if os.path.exists(baseline_path):
        with open(baseline_path, "r") as f:
            baseline = json.load(f)
        
        # Check regressions (>5% drop)
        for k, v in current_metrics.items():
            if k in baseline:
                drop = baseline[k] - v
                if drop > 0.05:
                    logger.error(f"REGRESSION DETECTED: {k} dropped from {baseline[k]:.3f} to {v:.3f} (-{drop:.3f})")
                    regression = True
    else:
        logger.info("No baseline found. Saving current metrics as baseline.")
        with open(baseline_path, "w") as f:
            json.dump(current_metrics, f, indent=2)

    passed_thresholds = True
    if run_phase_2:
        passed_thresholds = (
            avg_context_recall >= min_context_recall and
            avg_faithfulness >= min_faithfulness and
            avg_relevancy >= min_relevancy and
            avg_citation >= min_citation
        )
    
    passed = passed_thresholds and not regression
    
    # Summary Table
    summary = f"## 📊 RAG Evaluation Summary\n\n"
    summary += f"**Status:** {'✅ PASSED' if passed else '❌ FAILED'}\n\n"
    summary += "| Metric | Score | Threshold | Status |\n"
    summary += "|---|---|---|---|\n"
    summary += f"| Retrieval Recall@3 | {retrieval_recall:.3f} | - | {'✅' if not regression else '⚠️'} |\n"
    summary += f"| Retrieval MRR | {retrieval_mrr:.3f} | - | {'✅' if not regression else '⚠️'} |\n"
    
    if run_phase_2:
        summary += f"| Context Recall (RAGAS) | {avg_context_recall:.3f} | {min_context_recall} | {'✅' if avg_context_recall >= min_context_recall else '❌'} |\n"
        summary += f"| Faithfulness (RAGAS) | {avg_faithfulness:.3f} | {min_faithfulness} | {'✅' if avg_faithfulness >= min_faithfulness else '❌'} |\n"
        summary += f"| Answer Relevancy (RAGAS) | {avg_relevancy:.3f} | {min_relevancy} | {'✅' if avg_relevancy >= min_relevancy else '❌'} |\n"
        summary += f"| Citation Validity | {avg_citation:.3f} | {min_citation} | {'✅' if avg_citation >= min_citation else '❌'} |\n"
        summary += f"| Out-of-Corpus Safety | {ooc_score:.3f} | 1.0 | {'✅' if ooc_score == 1.0 else '❌'} |\n\n"
        
        metrics_df["avg_score"] = metrics_df[["context_recall", "faithfulness", "answer_relevancy"]].mean(axis=1)
        worst_row = metrics_df.loc[metrics_df["avg_score"].idxmin()]
        
        summary += f"### 📉 Worst Performing Question (Avg Score: {worst_row['avg_score']:.2f})\n"
        summary += f"- **Question:** {worst_row['question']}\n"
        summary += f"- **Answer:** {worst_row['answer']}\n"
    else:
        summary += "\n> ℹ️ **Notice:** Phase 2 (LLM Generation) was skipped. Only offline retrieval metrics are shown.\n\n"

    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a") as f:
            f.write(summary)
            
    with open("evals/eval_summary.md", "w") as f:
        f.write(summary)

    if not passed:
        logger.error("Quality thresholds or baseline regressions not met. Failing pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieval-only", action="store_true", help="Run only Phase 1 (Retrieval)")
    args = parser.parse_args()
    
    run_evaluation(retrieval_only=args.retrieval_only)

import os
import sys
import json
import statistics
from typing import List

# Setup path so we can import src
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

# Wrapper for RAGAS to use our local sentence-transformers model
class LangchainLocalEmbedderWrapper(Embeddings):
    def __init__(self, embedder: LocalEmbedder):
        self.embedder = embedder
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(texts)
        
    def embed_query(self, text: str) -> List[float]:
        return self.embedder.embed_query(text)

def run_rag_eval():
    logger.info("Initializing Quoris RAG pipeline for evaluation...")
    
    # 1. Initialize Pipeline components
    parser = MarkdownParser()
    chunker = SemanticCodeChunker()
    embedder = LocalEmbedder()
    
    vector_store = ChromaVectorStore(embedder=embedder)
    bm25 = LocalBM25Retriever()
    
    # Index corpus for BM25 and Vector DB
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
    
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY is not set. Evaluation requires the Groq API.")
        sys.exit(1)
        
    llm_generator = GroqLLMGenerator(api_key=GROQ_API_KEY)
    orchestrator = RAGOrchestrator(hybrid_retriever=hybrid_retriever, reranker=reranker, llm=llm_generator)
    
    # 2. Load Golden Dataset
    dataset_path = "evals/golden_dataset.json"
    if not os.path.exists(dataset_path):
        logger.error(f"Golden dataset not found at {dataset_path}")
        sys.exit(1)
        
    with open(dataset_path, "r", encoding="utf-8") as f:
        golden_data = json.load(f)
        
    logger.info(f"Loaded {len(golden_data)} evaluation questions.")
    
    # 3. Collect Answers and Contexts
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    for item in golden_data:
        q = item["query"]
        logger.info(f"Evaluating query: {q}")
        
        try:
            res = orchestrator.query(q)
            ans = res["answer"]
            ctx = [doc["content"] for doc in res["context_used"]]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            ans = f"Error: {e}"
            ctx = [""]
            
        questions.append(q)
        answers.append(ans)
        contexts.append(ctx)
        ground_truths.append(item["expected_answer"])
        
    # Build HuggingFace Dataset
    hf_dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })
    
    # 4. Setup RAGAS Evaluator (using Groq + Local Embedder)
    judge_llm = ChatGroq(model_name="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.0)
    judge_embeddings = LangchainLocalEmbedderWrapper(embedder=embedder)
    
    logger.info("Executing RAGAS evaluation...")
    # NOTE: ragas evaluate requires passing metrics, llm and embeddings explicitly to avoid OpenAI dependencies
    result = evaluate(
        hf_dataset,
        metrics=[context_recall, faithfulness, answer_relevancy],
        llm=judge_llm,
        embeddings=judge_embeddings
    )
    
    # Extract metrics
    metrics_df = result.to_pandas()
    avg_recall = metrics_df["context_recall"].mean() if "context_recall" in metrics_df else 0.0
    avg_faithfulness = metrics_df["faithfulness"].mean() if "faithfulness" in metrics_df else 0.0
    avg_relevancy = metrics_df["answer_relevancy"].mean() if "answer_relevancy" in metrics_df else 0.0
    
    logger.info(f"RAGAS Results - Recall: {avg_recall:.2f}, Faithfulness: {avg_faithfulness:.2f}, Relevancy: {avg_relevancy:.2f}")
    
    # 5. Check Thresholds
    min_recall = float(os.getenv("MIN_CONTEXT_RECALL", "0.75"))
    min_faithfulness = float(os.getenv("MIN_FAITHFULNESS", "0.80"))
    min_relevancy = float(os.getenv("MIN_ANSWER_RELEVANCY", "0.75"))
    
    passed = (
        avg_recall >= min_recall and
        avg_faithfulness >= min_faithfulness and
        avg_relevancy >= min_relevancy
    )
    
    # Identify worst performing question (lowest average score)
    metrics_df["avg_score"] = metrics_df[["context_recall", "faithfulness", "answer_relevancy"]].mean(axis=1)
    worst_row = metrics_df.loc[metrics_df["avg_score"].idxmin()]
    worst_q = worst_row["question"]
    worst_score = worst_row["avg_score"]
    
    # 6. Generate Markdown Report for GitHub Step Summary
    summary = f"## 📊 RAG Evaluation Summary\n\n"
    summary += f"**Status:** {'✅ PASSED' if passed else '❌ FAILED'}\n\n"
    summary += "| Metric | Score | Threshold | Status |\n"
    summary += "|---|---|---|---|\n"
    summary += f"| Context Recall | {avg_recall:.3f} | {min_recall} | {'✅' if avg_recall >= min_recall else '❌'} |\n"
    summary += f"| Faithfulness | {avg_faithfulness:.3f} | {min_faithfulness} | {'✅' if avg_faithfulness >= min_faithfulness else '❌'} |\n"
    summary += f"| Answer Relevancy | {avg_relevancy:.3f} | {min_relevancy} | {'✅' if avg_relevancy >= min_relevancy else '❌'} |\n\n"
    
    summary += f"### 📉 Worst Performing Question (Avg Score: {worst_score:.2f})\n"
    summary += f"- **Question:** {worst_q}\n"
    summary += f"- **Answer Generated:** {worst_row['answer']}\n"
    summary += f"- **Context Recall:** {worst_row['context_recall']:.2f}\n"
    summary += f"- **Faithfulness:** {worst_row['faithfulness']:.2f}\n"
    summary += f"- **Answer Relevancy:** {worst_row['answer_relevancy']:.2f}\n"

    # Write to GITHUB_STEP_SUMMARY if available
    step_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        with open(step_summary_file, "a", encoding="utf-8") as f:
            f.write(summary)
            
    # Also save it to a local markdown file for the PR comment workflow
    with open("evals/eval_summary.md", "w", encoding="utf-8") as f:
        f.write(summary)
            
    if not passed:
        logger.error("Quality thresholds not met. Failing the pipeline.")
        # List questions that failed significantly (< 0.5 average)
        failures = metrics_df[metrics_df["avg_score"] < 0.5]
        if not failures.empty:
            logger.error("Severely failing questions:")
            for _, row in failures.iterrows():
                logger.error(f"- {row['question']} (Score: {row['avg_score']:.2f})")
        sys.exit(1)
        
    logger.info("Evaluation passed successfully.")
    
if __name__ == "__main__":
    run_rag_eval()

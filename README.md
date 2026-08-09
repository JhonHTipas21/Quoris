# Quoris

Quoris is an advanced Retrieval-Augmented Generation (RAG) conversational assistant specifically designed to query and answer questions about payment API documentation, including Wompi, Stripe, and Mercado Pago. It implements a production-grade 7-layer architecture, ensuring high precision, source citation, and mitigation of hallucination risks inherent in standard LLMs.

## Architecture

Unlike naive RAG systems, Quoris utilizes a 7-step pipeline to guarantee accuracy and traceability:

1. **Process & Parse**: A custom code-block-aware Markdown parser extracts headers, preserves code blocks, and builds hierarchical metadata paths to retain document context.
2. **Chunk**: The semantic chunker splits documents into manageable pieces (500-800 characters) while prepending header paths to maintain context and preventing the truncation of code snippets.
3. **Embed**: Local embeddings are generated utilizing `all-MiniLM-L6-v2` via SentenceTransformers for fast, cost-effective vector representation.
4. **Store**: A Chroma vector database stores embeddings with an incremental update mechanism based on MD5 content hashing to avoid redundant processing.
5. **Query (Hybrid Retrieval)**: 
   - **Dense Retrieval**: Semantic vector search via Chroma.
   - **Sparse Retrieval**: Lexical keyword search via BM25Okapi, featuring zero-score filtering and metadata routing.
   - **Fusion**: Both strategies are merged using Reciprocal Rank Fusion (RRF) to maximize recall.
6. **Rerank**: A local Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) re-evaluates and strictly ranks the top candidates retrieved by the hybrid search.
7. **Generate**: The Groq API (Llama 3.3 70B) generates the final response, employing strict grounding prompts and incorporating exact footnote citations (URL and section) to ensure traceability.

## Project Structure

```
Quoris/
├── docs/                 # Payment API documentation corpus (Wompi, Stripe, MercadoPago)
├── src/                  # Core RAG pipeline modules
│   ├── api.py            # FastAPI server exposing querying endpoints
│   ├── chunker.py        # Semantic markdown chunker
│   ├── cli.py            # Command-line interface for Chroma DB management
│   ├── config.py         # Application configuration and paths
│   ├── document.py       # Pydantic schema for documents with hashing
│   ├── embedder.py       # Local SentenceTransformers embedder
│   ├── index_docs.py     # Batch ingestion script
│   ├── interfaces.py     # Abstract Base Classes (SOLID principles)
│   ├── logger.py         # Structured logging configuration
│   ├── orchestrator.py   # Main 7-layer pipeline orchestrator
│   ├── parser.py         # Markdown hierarchical parser
│   ├── reranker.py       # Cross-Encoder reranking implementation
│   ├── retriever.py      # BM25 and Hybrid retrieval with RRF
│   ├── rewriter.py       # LLM-based query expansion and rewriting
│   └── vector_store.py   # Chroma DB wrapper with incremental updates
├── tests/                # Comprehensive test suites for all modules
├── evals/                # Evaluation pipeline, baseline metrics, and golden datasets
├── frontend/             # Streamlit interactive user interface
└── requirements.txt      # Project dependencies
```

## Setup and Installation

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   Copy `.env.example` to `.env` and configure the required keys, primarily the `GROQ_API_KEY`.

3. Initialize the Vector Database:
   ```bash
   python src/cli.py index
   ```

## Usage

### Command Line Interface (CLI)
Manage the Chroma database directly from the terminal:
```bash
# Check database status and chunk count
python src/cli.py status

# Run a test query against the vector store
python src/cli.py query --text "webhook signature validation" -k 3

# Wipe the database collections
python src/cli.py wipe
```

### API Server
Start the FastAPI backend:
```bash
uvicorn src.api:app --reload --port 8000
```

### User Interface
Launch the Streamlit frontend:
```bash
streamlit run frontend/app.py
```

## Testing and Evaluation
Execute the unit testing suite:
```bash
pytest tests/ -v
```

Execute the offline evaluation pipeline to compute Recall, MRR, and baseline regression metrics against the golden dataset:
```bash
# Run retrieval evaluation only (Phase 1)
python evals/run_rag_eval.py --retrieval-only

# Run full generation and RAGAS evaluation (Phase 2)
python evals/run_rag_eval.py
```

## Continuous Integration
The repository includes two GitHub Actions workflows:

*   **PR Evaluation Workflow (`.github/workflows/rag-ci.yml`)**: Runs automatically on pull requests that modify source code, documentation, prompts, or evaluation datasets.
    *   **Fork Security**: If a pull request originates from a fork, it executes in offline mode (Phase 1) to evaluate retrieval (Recall@3, MRR) without exposing API secrets.
    *   **Internal PRs**: Executes the full pipeline, calculating retrieval and RAGAS generation metrics (context_recall, faithfulness, answer_relevancy, citation_validity), posting the final markdown summary as a PR comment.
    *   **Chroma Cache**: Embeddings cache is managed dynamically based on document hashes.
*   **Nightly Regression Workflow (`.github/workflows/rag-nightly.yml`)**: Runs nightly to benchmark the main branch against the baseline (`evals/baseline_metrics.json`).
    *   If a quality metric drops by more than 5%, a GitHub issue is automatically created or commented on to notify the team of a RAG regression.
    *   Threshold configurations default to: MIN_CONTEXT_RECALL=0.75, MIN_FAITHFULNESS=0.80, MIN_ANSWER_RELEVANCY=0.75, MIN_CITATION_VALIDITY=0.90.

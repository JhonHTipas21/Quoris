---
name: hybrid-query
description: Execute hybrid retrieval, rewrite queries, merge with RRF, rerank candidates, and generate grounded answers.
---
# Hybrid Query and Generation Skill

This skill describes the runtime retrieval, ranking, and response generation pipeline.

## Flow of Query Execution

1. **Query Expansion / Rewriting (src/rewriter.py)**: The raw query is expanded via LLM query rewriting to include technical synonyms and resolve abbreviations.
2. **Hybrid Retrieval (src/retriever.py)**:
   - **Dense Search**: Semantic vector cosine similarity in Chroma DB.
   - **Sparse Search**: BM25 Okapi lexical matching. Filters out zero-score matches.
   - **Fusion**: Combines rank lists using Reciprocal Rank Fusion (RRF).
3. **Reranking (src/reranker.py)**: Employs a local Cross-Encoder (ms-marco-MiniLM-L-6-v2) to re-score and select the top 3 chunks.
4. **Generation (src/llm.py)**: Sends the top chunks and rewritten query to Groq (Llama 3.3 70b) with strict formatting instructions (adding footnoted citations [Doc X]).

---
name: ingest-corpus
description: Parse hierarchical Markdown docs, perform semantic code-aware chunking, and index into Chroma vector database.
---
# Corpus Ingestion Skill

This skill documents how payment documentation corpus is parsed, chunked, and indexed.

## Commands

- Run full document ingestion & indexing CLI:
  ```bash
  .venv/bin/python src/cli.py index
  ```
- Check Chroma DB status:
  ```bash
  .venv/bin/python src/cli.py status
  ```
- Wipe Chroma collections:
  ```bash
  .venv/bin/python src/cli.py wipe
  ```

## Ingestion Architecture

1. **Parser (src/parser.py)**: Uses MarkdownParser to split documents by headers while preserving hierarchical metadata path to maintain document context.
2. **Chunker (src/chunker.py)**: Uses SemanticCodeChunker to split parsed markdown sections into chunks (500-800 characters) while prepending header hierarchies to prevent context drift and keeping code blocks intact.
3. **Database (src/vector_store.py)**: Indexes embeddings using LocalEmbedder (SentenceTransformers). Implements incremental upserts using MD5 content hashing.

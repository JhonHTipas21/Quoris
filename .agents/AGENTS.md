# Quoris Agent Guidelines

This document outlines structural rules and coding guidelines for modifying the Quoris 7-layer RAG pipeline.

## Architectural Integrity

- **No Framework Swapping**: Do not replace LangChain with LlamaIndex, nor Chroma with another vector store, unless specifically authorized.
- **Strict Grounding**: Prompt templates must enforce that the model refuses to answer ("No tengo información suficiente") when query terms cannot be found in the retrieved context.
- **No Emojis**: All documentation, comments, markdown, and commits must be professional, concrete, and completely emoji-free.
- **English Codebase**: Keep all comments, logs, and naming in English.

## PR and CI/CD Rules

- **Fork-Safety**: All PR workflows must separate retrieval-only offline tests from API-dependent tests to support forks securely.
- **Incremental Cache**: Chroma cache in CI should be dependent on the hash of `docs/**/*.md` and `requirements.txt`.

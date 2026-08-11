---
name: rag-eval
description: Execute and analyze RAG pipeline retrieval and generation evaluations using RAGAS and baseline metrics.
---
# RAG Evaluation Skill

This skill explains how to run, validate, and maintain the continuous evaluation system for Quoris.

## Commands

- Run retrieval evaluation only (fast/offline):
  ```bash
  .venv/bin/python evals/run_rag_eval.py --retrieval-only
  ```
- Run full evaluation (Retrieval + LLM generation/RAGAS):
  ```bash
  .venv/bin/python evals/run_rag_eval.py
  ```

## Flow and Guidelines

1. **Baseline Regression Check**: The evaluation script compares current metrics against `evals/baseline_metrics.json`. If any metric drops by more than 5% (0.05), it flags a regression and exits with code 1.
2. **Quality Thresholds**:
   - MIN_CONTEXT_RECALL=0.75
   - MIN_FAITHFULNESS=0.80
   - MIN_ANSWER_RELEVANCY=0.75
   - MIN_CITATION_VALIDITY=0.90
3. **Citation Validity**: Ensure that every citation reference in the answer (e.g., [Doc X]) maps to an actual chunk in the top-N retrieved context.
4. **Out-of-Corpus Safety**: Queries with no relevant documentation must return "No tengo información suficiente" instead of hallucinating.

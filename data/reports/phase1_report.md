# Phase 1: Baseline Data Pipeline & RAG Evaluation Report

## 1. Source Summary
- **Source API:** Crossref REST API
- **Query:** `agentic retrieval augmented generation large language model`
- **Filter:** `from-pub-date:2025-12-12,has-abstract:true`
- **Max Results:** 24
- **Total Records Parsed:** 23

## 2. Evaluation Metrics
| Metric | Value |
| --- | --- |
| **Retrieval Hit Rate** | 0.0000 |
| **Mean Token F1** | 0.0000 |
| **Judge Accuracy** | 0.0000 |
| **Mean Judge Score** | 1.0000 |

## 3. Data Quality Status
- **Overall Quality Passed:** ✅ YES
- **Quality Summary:**
  - Total Checks: 14
  - Passed: 14
  - Failed: 0

## 4. Freshness Status
- **Is Fresh:** ✅ YES
- **Stale Rows:** 0 / 23
- **Threshold Days:** 180 days
- **Latest Published Date:** 2026-06-02
- **Oldest Published Date:** 2025-12-19

## 5. Artifacts
- **Raw API Response:** `data/raw/crossref_response.json`
- **Cleaned Data:** `data/clean/papers_clean.csv` / `data/clean/papers_clean.json`
- **Chroma Directory:** `data/chroma/`
- **Embeddings Manifest:** `data/embeddings/papers_embeddings.json`
- **Evaluation Test Set:** `data/eval/test_set.json`
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Quality Report:** `data/quality/baseline_quality.json`
- **Freshness Report:** `data/quality/freshness_report.json`

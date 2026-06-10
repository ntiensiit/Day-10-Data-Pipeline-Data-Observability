# Phase 1: Baseline Data Pipeline & RAG Evaluation Report

## 1. Source Summary
- **Source API:** Crossref
- **Query:** `q`
- **Filter:** `f`
- **Max Results:** 2
- **Total Records Parsed:** 2

## 2. Evaluation Metrics
| Metric | Value |
| --- | --- |
| **Retrieval Hit Rate** | 1.0000 |
| **Mean Token F1** | 1.0000 |
| **Judge Accuracy** | 1.0000 |
| **Mean Judge Score** | 5.0000 |

## 3. Data Quality Status
- **Overall Quality Passed:** ❌ NO
- **Quality Summary:**
  - Total Checks: 14
  - Passed: 12
  - Failed: 2

## 4. Freshness Status
- **Is Fresh:** ❌ NO
- **Stale Rows:** 2 / 2
- **Threshold Days:** 180 days
- **Latest Published Date:** 2023-07-08
- **Oldest Published Date:** 2023-07-08

## 5. Artifacts
- **Raw API Response:** `data/raw/crossref_response.json`
- **Cleaned Data:** `data/clean/papers_clean.csv` / `data/clean/papers_clean.json`
- **Chroma Directory:** `data/chroma/`
- **Embeddings Manifest:** `data/embeddings/papers_embeddings.json`
- **Evaluation Test Set:** `data/eval/test_set.json`
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Quality Report:** `data/quality/baseline_quality.json`
- **Freshness Report:** `data/quality/freshness_report.json`

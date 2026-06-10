# Data Pipeline Corruption & Recovery Comparison Report

- **Run ID:** 20260610T084000Z
- **Created At:** 2026-06-10T08:40:36Z

## 1. Metrics Comparison
| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| **Retrieval Hit Rate** | 0.0000 | 0.0000 | 0.0000 |
| **Mean Token F1** | 0.0000 | 0.0000 | 0.0000 |
| **Judge Accuracy** | 0.0000 | 0.0000 | 0.0000 |
| **Mean Judge Score** | 1.0000 | 1.0000 | 1.0000 |

## 2. Observability Report
| Metric / Check | Corrupted Pipeline | Repaired Pipeline |
| --- | --- | --- |
| **Hard Quality Passed** | ❌ Failed | ✅ Passed |
| **Failed Hard Checks** | 2 / 11 | 0 / 11 |
| **Warnings Triggered** | 5 / 9 | 2 / 9 |
| **Freshness (Is Fresh)** | ❌ Stale | ✅ Fresh |
| **Stale Rows** | 1 / 22 | 0 / 23 |

## 3. Artifact Paths
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Corrupted Metrics:** `data/results/corrupted_metrics.json`
- **Repaired Metrics:** `data/results/repaired_metrics.json`
- **Corrupted Quality Report:** `data/quality/corrupted_quality.json`
- **Repaired Quality Report:** `data/quality/repaired_quality.json`
- **Corrupted Freshness Report:** `data/quality/corrupted_freshness_report.json`
- **Repaired Freshness Report:** `data/quality/repaired_freshness_report.json`

## 4. Interpretation of Corruption Impact
The injected corruption produced observable impact: hard quality checks failed; 5 warnings triggered; freshness report flagged stale rows.

## 5. Interpretation of Repair Recovery
Rebuilding from raw Crossref records produced a repaired dataset, and the observability artifacts confirm hard quality and freshness passed.

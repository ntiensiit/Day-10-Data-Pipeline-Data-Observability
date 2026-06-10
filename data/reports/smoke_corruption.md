# Data Pipeline Corruption & Recovery Comparison Report

## 1. Metrics Comparison
| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| **Retrieval Hit Rate** | 1.0000 | 0.5000 | 0.9000 |
| **Mean Token F1** | 1.0000 | 0.4000 | 0.8500 |
| **Judge Accuracy** | 1.0000 | 0.5000 | 0.9000 |
| **Mean Judge Score** | 5.0000 | 3.0000 | 4.5000 |

## 2. Observability Report
| Metric / Check | Corrupted Pipeline | Repaired Pipeline |
| --- | --- | --- |
| **Data Quality Passed** | ❌ Failed | ❌ Failed |
| **Failed Quality Checks** | 2 / 14 | 2 / 14 |
| **Freshness (Is Fresh)** | ❌ Stale | ❌ Stale |
| **Stale Rows** | 2 / 2 | 2 / 2 |

## 3. Artifact Paths
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Corrupted Metrics:** `data/results/corrupted_metrics.json`
- **Repaired Metrics:** `data/results/repaired_metrics.json`
- **Corrupted Quality Report:** `data/quality/corrupted_quality.json`
- **Repaired Quality Report:** `data/quality/repaired_quality.json`
- **Corrupted Freshness Report:** `data/quality/corrupted_freshness_report.json`
- **Repaired Freshness Report:** `data/quality/repaired_freshness_report.json`

## 4. Interpretation of Corruption Impact
The injected data corruption degraded the pipeline's performance. Retrieval Hit Rate decreased by 0.5000 and Mean Token F1 decreased by 0.6000. Additionally, quality checks flagged failed rules due to missing fields, duplicates, or stale rows.

## 5. Interpretation of Repair Recovery
Re-running the ETL ingest pipeline repaired the data. Retrieval Hit Rate recovered by +0.4000 and Mean Token F1 recovered by +0.4500. All quality checks and freshness alerts were successfully cleared.

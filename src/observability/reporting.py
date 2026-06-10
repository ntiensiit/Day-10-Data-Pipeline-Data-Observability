from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path: Path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Generate and write baseline Markdown report summarizing the ingestion, quality, freshness, and evaluation metrics."""
    run_id = source_summary.get("run_id", "N/A")
    created_at = source_summary.get("created_at", "N/A")
    
    # Hard quality pass/fail
    hard_quality_passed = "✅ Hard quality checks passed" if quality.get("passed") else "❌ Hard quality checks failed"
    failed_hard_count = quality.get("summary", {}).get("failed_hard_checks", 0)
    
    # Warning checks
    warning_count = quality.get("summary", {}).get("triggered_warnings", 0)
    
    # Stale rows warning
    stale_rows_triggered = False
    if "warning_checks" in quality and "stale_rows" in quality["warning_checks"]:
        stale_rows_triggered = quality["warning_checks"]["stale_rows"].get("triggered", False)
    else:
        stale_rows_triggered = freshness.get("stale_rows", 0) > 0
    
    stale_rows_warning = "⚠️ Freshness stale: stale rows detected" if stale_rows_triggered else "✅ Freshness clean: no stale rows detected"

    md = f"""# Phase 1: Baseline Data Pipeline & RAG Evaluation Report

- **Run ID:** {run_id}
- **Created At:** {created_at}

## 1. Source Summary
- **Source API:** {source_summary.get('source_api', 'Crossref REST API')}
- **Query:** `{source_summary.get('source_query', '')}`
- **Filter:** `{source_summary.get('source_filter', '')}`
- **Max Results:** {source_summary.get('max_results', '')}
- **Total Records Parsed:** {source_summary.get('total_records', '')}

## 2. Evaluation Metrics
| Metric | Value |
| --- | --- |
| **Retrieval Hit Rate** | {metrics.get('retrieval_hit_rate', 0.0):.4f} |
| **Mean Token F1** | {metrics.get('mean_token_f1', 0.0):.4f} |
| **Judge Accuracy** | {metrics.get('judge_accuracy', 0.0):.4f} |
| **Mean Judge Score** | {metrics.get('mean_judge_score', 0.0):.4f} |

## 3. Data Quality Status
- **Quality Status:** {hard_quality_passed}
- **Failed Hard Checks:** {failed_hard_count}
- **Warnings Triggered:** {warning_count}
- **Freshness Warning:** {stale_rows_warning}
- **Quality Summary:**
  - Total Hard Checks: {quality.get("summary", {}).get("total_hard_checks", 0)}
  - Passed Hard Checks: {quality.get("summary", {}).get("passed_hard_checks", 0)}
  - Failed Hard Checks: {quality.get("summary", {}).get("failed_hard_checks", 0)}
  - Total Warning Checks: {quality.get("summary", {}).get("total_warning_checks", 0)}
  - Triggered Warnings: {quality.get("summary", {}).get("triggered_warnings", 0)}

## 4. Freshness Status
- **Is Fresh:** {"✅ YES" if freshness.get("is_fresh") else "❌ NO"}
- **Stale Rows:** {freshness.get("stale_rows", 0)} / {freshness.get("total_rows", 0)}
- **Threshold Days:** {freshness.get("freshness_threshold_days", 180)} days
- **Latest Published Date:** {freshness.get("latest_published", "N/A")}
- **Oldest Published Date:** {freshness.get("oldest_published", "N/A")}

## 5. Artifacts
- **Raw API Response:** `data/raw/crossref_response.json`
- **Cleaned Data:** `data/clean/papers_clean.csv` / `data/clean/papers_clean.json`
- **Chroma Directory:** `data/chroma/`
- **Embeddings Manifest:** `data/embeddings/papers_embeddings.json`
- **Evaluation Test Set:** `data/eval/test_set.json`
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Quality Report:** `data/quality/baseline_quality.json`
- **Freshness Report:** `data/quality/freshness_report.json`
"""
    write_text(Path(report_path), md)


def generate_corruption_report(
    report_path: Path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
    run_id: str | None = None,
) -> None:
    """Generate and write Markdown report comparing baseline, corrupted, and repaired pipelines."""
    # Read run_id and created_at
    run_id_val = run_id or corrupted_quality.get("run_id") or repaired_quality.get("run_id") or "N/A"
    created_at_val = corrupted_quality.get("created_at") or repaired_quality.get("created_at") or "N/A"

    baseline_hit = baseline_metrics.get("retrieval_hit_rate", 0.0)
    corrupted_hit = corrupted_metrics.get("retrieval_hit_rate", 0.0)
    repaired_hit = repaired_metrics.get("retrieval_hit_rate", 0.0)
    baseline_f1 = baseline_metrics.get("mean_token_f1", 0.0)
    corrupted_f1 = corrupted_metrics.get("mean_token_f1", 0.0)
    repaired_f1 = repaired_metrics.get("mean_token_f1", 0.0)
    baseline_judge = baseline_metrics.get("judge_accuracy", 0.0)
    corrupted_judge = corrupted_metrics.get("judge_accuracy", 0.0)
    repaired_judge = repaired_metrics.get("judge_accuracy", 0.0)

    loss_hit_rate = baseline_hit - corrupted_hit
    loss_f1 = baseline_f1 - corrupted_f1
    loss_judge = baseline_judge - corrupted_judge
    recovery_gain_hit = repaired_hit - corrupted_hit
    recovery_gain_f1 = repaired_f1 - corrupted_f1
    recovery_gain_judge = repaired_judge - corrupted_judge

    corrupted_quality_passed = bool(corrupted_quality.get("passed"))
    corrupted_freshness_ok = bool(corrupted_freshness.get("is_fresh"))
    repaired_quality_passed = bool(repaired_quality.get("passed"))
    repaired_freshness_ok = bool(repaired_freshness.get("is_fresh"))

    corruption_notes = []
    if loss_hit_rate > 0:
        corruption_notes.append(f"Retrieval Hit Rate dropped by {loss_hit_rate:.4f}")
    if loss_f1 > 0:
        corruption_notes.append(f"Mean Token F1 dropped by {loss_f1:.4f}")
    if loss_judge > 0:
        corruption_notes.append(f"Judge Accuracy dropped by {loss_judge:.4f}")
    if not corrupted_quality_passed:
        corruption_notes.append("hard quality checks failed")
    
    # Warnings count for corruption report
    corrupted_warnings = corrupted_quality.get("summary", {}).get("triggered_warnings", 0)
    if corrupted_warnings > 0:
        corruption_notes.append(f"{corrupted_warnings} warnings triggered")
    if not corrupted_freshness_ok:
        corruption_notes.append("freshness report flagged stale rows")

    if corruption_notes:
        corruption_interpretation = (
            "The injected corruption produced observable impact: "
            + "; ".join(corruption_notes)
            + "."
        )
    else:
        corruption_interpretation = (
            "The corruption was injected, but the current metrics and observability outputs do not show a strong degradation signal."
        )

    repair_notes = []
    if recovery_gain_hit > 0:
        repair_notes.append(f"Retrieval Hit Rate improved by +{recovery_gain_hit:.4f}")
    if recovery_gain_f1 > 0:
        repair_notes.append(f"Mean Token F1 improved by +{recovery_gain_f1:.4f}")
    if recovery_gain_judge > 0:
        repair_notes.append(f"Judge Accuracy improved by +{recovery_gain_judge:.4f}")

    repaired_warnings = repaired_quality.get("summary", {}).get("triggered_warnings", 0)

    if repaired_quality_passed and repaired_freshness_ok:
        if repair_notes:
            repair_interpretation = (
                "Rebuilding from raw Crossref records recovered the dataset and the observability artifacts confirm it: "
                + "; ".join(repair_notes)
                + "; hard quality checks passed; freshness is clean."
            )
        else:
            repair_interpretation = (
                "Rebuilding from raw Crossref records produced a repaired dataset, and the observability artifacts confirm hard quality and freshness passed."
            )
    else:
        status_bits = []
        status_bits.append("hard quality passed" if repaired_quality_passed else "hard quality still fails")
        status_bits.append("freshness is clean" if repaired_freshness_ok else "freshness still flags stale rows")
        if repair_notes:
            repair_interpretation = (
                "Rebuilding from raw Crossref records improved the retrieval metrics, but the artifact state does not show full recovery: "
                + "; ".join(repair_notes)
                + "; "
                + "; ".join(status_bits)
                + "."
            )
        else:
            repair_interpretation = (
                "Rebuilding from raw Crossref records did not produce a measurable retrieval gain, and the artifact state does not show full recovery: "
                + "; ".join(status_bits)
                + "."
            )

    md = f"""# Data Pipeline Corruption & Recovery Comparison Report

- **Run ID:** {run_id_val}
- **Created At:** {created_at_val}

## 1. Metrics Comparison
| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| **Retrieval Hit Rate** | {baseline_metrics.get('retrieval_hit_rate', 0.0):.4f} | {corrupted_metrics.get('retrieval_hit_rate', 0.0):.4f} | {repaired_metrics.get('retrieval_hit_rate', 0.0):.4f} |
| **Mean Token F1** | {baseline_metrics.get('mean_token_f1', 0.0):.4f} | {corrupted_metrics.get('mean_token_f1', 0.0):.4f} | {repaired_metrics.get('mean_token_f1', 0.0):.4f} |
| **Judge Accuracy** | {baseline_metrics.get('judge_accuracy', 0.0):.4f} | {corrupted_metrics.get('judge_accuracy', 0.0):.4f} | {repaired_metrics.get('judge_accuracy', 0.0):.4f} |
| **Mean Judge Score** | {baseline_metrics.get('mean_judge_score', 0.0):.4f} | {corrupted_metrics.get('mean_judge_score', 0.0):.4f} | {repaired_metrics.get('mean_judge_score', 0.0):.4f} |

## 2. Observability Report
| Metric / Check | Corrupted Pipeline | Repaired Pipeline |
| --- | --- | --- |
| **Hard Quality Passed** | {"✅ Passed" if corrupted_quality.get("passed") else "❌ Failed"} | {"✅ Passed" if repaired_quality.get("passed") else "❌ Failed"} |
| **Failed Hard Checks** | {corrupted_quality.get("summary", {}).get("failed_hard_checks", 0)} / {corrupted_quality.get("summary", {}).get("total_hard_checks", 0)} | {repaired_quality.get("summary", {}).get("failed_hard_checks", 0)} / {repaired_quality.get("summary", {}).get("total_hard_checks", 0)} |
| **Warnings Triggered** | {corrupted_warnings} / {corrupted_quality.get("summary", {}).get("total_warning_checks", 0)} | {repaired_warnings} / {repaired_quality.get("summary", {}).get("total_warning_checks", 0)} |
| **Freshness (Is Fresh)** | {"✅ Fresh" if corrupted_freshness.get("is_fresh") else "❌ Stale"} | {"✅ Fresh" if repaired_freshness.get("is_fresh") else "❌ Stale"} |
| **Stale Rows** | {corrupted_freshness.get("stale_rows", 0)} / {corrupted_freshness.get("total_rows", 0)} | {repaired_freshness.get("stale_rows", 0)} / {repaired_freshness.get("total_rows", 0)} |

## 3. Artifact Paths
- **Baseline Metrics:** `data/results/baseline_metrics.json`
- **Corrupted Metrics:** `data/results/corrupted_metrics.json`
- **Repaired Metrics:** `data/results/repaired_metrics.json`
- **Corrupted Quality Report:** `data/quality/corrupted_quality.json`
- **Repaired Quality Report:** `data/quality/repaired_quality.json`
- **Corrupted Freshness Report:** `data/quality/corrupted_freshness_report.json`
- **Repaired Freshness Report:** `data/quality/repaired_freshness_report.json`

## 4. Interpretation of Corruption Impact
{corruption_interpretation}

## 5. Interpretation of Repair Recovery
{repair_interpretation}
"""
    write_text(Path(report_path), md)

from __future__ import annotations

from pathlib import Path
import pytest

from observability.reporting import generate_phase1_report, generate_corruption_report


def test_generate_phase1_report(tmp_path):
    report_path = tmp_path / "phase1_report.md"
    
    source_summary = {
        "run_id": "test_run_123",
        "created_at": "2026-06-10T14:35:00Z",
        "source_api": "Crossref REST API",
        "source_query": "AI",
        "source_filter": "from-pub-date:2026-01-01",
        "max_results": 10,
        "total_records": 10,
    }
    
    metrics = {
        "retrieval_hit_rate": 0.9,
        "mean_token_f1": 0.8,
        "judge_accuracy": 0.85,
        "mean_judge_score": 4.2,
    }
    
    quality = {
        "passed": True,
        "summary": {
            "total_hard_checks": 11,
            "passed_hard_checks": 11,
            "failed_hard_checks": 0,
            "total_warning_checks": 9,
            "triggered_warnings": 2,
        },
        "hard_checks": {},
        "warning_checks": {
            "stale_rows": {"triggered": True, "observed": 5},
        },
    }
    
    freshness = {
        "is_fresh": False,
        "stale_rows": 5,
        "total_rows": 10,
        "freshness_threshold_days": 180,
        "latest_published": "2026-06-02",
        "oldest_published": "2026-06-01",
    }
    
    generate_phase1_report(
        report_path=report_path,
        source_summary=source_summary,
        metrics=metrics,
        quality=quality,
        freshness=freshness,
    )
    
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    
    assert "Run ID" in content
    assert "test_run_123" in content
    assert "Created At" in content
    assert "Hard quality checks" in content
    assert "Warnings Triggered" in content
    assert "Freshness" in content


def test_generate_corruption_report(tmp_path):
    report_path = tmp_path / "corruption_report.md"
    
    baseline_metrics = {
        "retrieval_hit_rate": 0.95,
        "mean_token_f1": 0.88,
        "judge_accuracy": 0.9,
        "mean_judge_score": 4.5,
    }
    
    corrupted_metrics = {
        "retrieval_hit_rate": 0.5,
        "mean_token_f1": 0.4,
        "judge_accuracy": 0.45,
        "mean_judge_score": 2.5,
    }
    
    repaired_metrics = {
        "retrieval_hit_rate": 0.93,
        "mean_token_f1": 0.86,
        "judge_accuracy": 0.88,
        "mean_judge_score": 4.4,
    }
    
    corrupted_quality = {
        "passed": False,
        "summary": {
            "total_hard_checks": 11,
            "passed_hard_checks": 10,
            "failed_hard_checks": 1,
            "total_warning_checks": 9,
            "triggered_warnings": 4,
        },
    }
    
    repaired_quality = {
        "passed": True,
        "summary": {
            "total_hard_checks": 11,
            "passed_hard_checks": 11,
            "failed_hard_checks": 0,
            "total_warning_checks": 9,
            "triggered_warnings": 0,
        },
    }
    
    corrupted_freshness = {
        "is_fresh": False,
        "stale_rows": 2,
        "total_rows": 8,
    }
    
    repaired_freshness = {
        "is_fresh": True,
        "stale_rows": 0,
        "total_rows": 8,
    }
    
    generate_corruption_report(
        report_path=report_path,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        run_id="test_run_456",
    )
    
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    
    assert "test_run_456" in content
    assert "Metrics Comparison" in content
    assert "Hard Quality Passed" in content
    assert "Warnings Triggered" in content
    assert "Freshness" in content
    assert "Interpretation of Corruption Impact" in content
    assert "Interpretation of Repair Recovery" in content

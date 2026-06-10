from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import pandas as pd
import pytest

from core.config import load_settings
from observability.quality import run_data_quality_checks, build_freshness_report


@pytest.fixture
def test_settings(tmp_path):
    settings = load_settings()
    test_paths = replace(
        settings.paths,
        quality_dir=tmp_path,
        freshness_report=tmp_path / "freshness_report.json"
    )
    return replace(settings, paths=test_paths)


@pytest.fixture
def clean_df():
    return pd.DataFrame([
        {
            "paper_id": "10.1000/1",
            "title": "A Great Title",
            "summary": "This is a summary of the paper. It has enough characters to pass the checks.",
            "summary_chars": 73,
            "authors_joined": "Author One",
            "categories_joined": "CS",
            "abs_url": "http://example.com/1",
            "pdf_url": "http://example.com/1.pdf",
            "published": "2026-06-01",
            "age_days": 10,
            "text_for_embedding": "Title: A Great Title\nSummary: This is a summary of the paper."
        },
        {
            "paper_id": "10.1000/2",
            "title": "Another Great Title",
            "summary": "This is another summary of the paper. It also has enough characters.",
            "summary_chars": 67,
            "authors_joined": "Author Two",
            "categories_joined": "CS",
            "abs_url": "http://example.com/2",
            "pdf_url": "http://example.com/2.pdf",
            "published": "2026-06-02",
            "age_days": 9,
            "text_for_embedding": "Title: Another Great Title\nSummary: This is another summary of the paper."
        }
    ])


def test_run_data_quality_checks_clean_data(clean_df, test_settings):
    report = run_data_quality_checks(clean_df, test_settings, "test_clean_report")
    
    # Test run_data_quality_checks() returns dictionary
    assert isinstance(report, dict)

    # Test report includes: report_name, passed, checks, summary, hard_checks, warning_checks
    assert report["report_name"] == "test_clean_report"
    assert "passed" in report
    assert "checks" in report
    assert "summary" in report
    assert "hard_checks" in report
    assert "warning_checks" in report
    
    # Test clean DataFrame passes hard checks
    assert report["passed"] is True
    assert report["summary"]["failed_hard_checks"] == 0
    assert report["summary"]["triggered_warnings"] == 0


def test_run_data_quality_checks_empty_df(test_settings):
    empty_df = pd.DataFrame(columns=[
        "paper_id", "title", "summary", "summary_chars",
        "authors_joined", "categories_joined", "abs_url",
        "pdf_url", "published", "age_days", "text_for_embedding"
    ])
    
    report = run_data_quality_checks(empty_df, test_settings, "test_empty_report")
    # Empty DataFrame fails row count check, so passed is False
    assert report["passed"] is False
    assert report["hard_checks"]["row_count_above_zero"]["passed"] is False


def test_run_data_quality_checks_missing_columns(clean_df, test_settings):
    # Test missing paper_id column fails
    df_no_id = clean_df.drop(columns=["paper_id"])
    report = run_data_quality_checks(df_no_id, test_settings, "test_no_id_report")
    assert report["passed"] is False
    assert report["hard_checks"]["paper_id_column_exists"]["passed"] is False

    # Test missing title column fails
    df_no_title = clean_df.drop(columns=["title"])
    report = run_data_quality_checks(df_no_title, test_settings, "test_no_title_report")
    assert report["passed"] is False
    assert report["hard_checks"]["title_column_exists"]["passed"] is False

    # Test missing summary column fails
    df_no_summary = clean_df.drop(columns=["summary"])
    report = run_data_quality_checks(df_no_summary, test_settings, "test_no_summary_report")
    assert report["passed"] is False
    assert report["hard_checks"]["summary_column_exists"]["passed"] is False

    # Test missing text_for_embedding column fails
    df_no_embed = clean_df.drop(columns=["text_for_embedding"])
    report = run_data_quality_checks(df_no_embed, test_settings, "test_no_embed_report")
    assert report["passed"] is False
    assert report["hard_checks"]["text_for_embedding_exists"]["passed"] is False


def test_run_data_quality_checks_invalid_values(clean_df, test_settings):
    # Test null paper_id fails
    df_null_id = clean_df.copy()
    df_null_id.loc[0, "paper_id"] = None
    report = run_data_quality_checks(df_null_id, test_settings, "test_null_id_report")
    assert report["passed"] is False
    assert report["hard_checks"]["paper_id_has_no_nulls"]["passed"] is False

    # Test duplicate paper_id fails
    df_dup_id = clean_df.copy()
    df_dup_id.loc[1, "paper_id"] = df_dup_id.loc[0, "paper_id"]
    report = run_data_quality_checks(df_dup_id, test_settings, "test_dup_id_report")
    assert report["passed"] is False
    assert report["hard_checks"]["paper_id_is_unique"]["passed"] is False


def test_run_data_quality_checks_warnings(clean_df, test_settings):
    # Test short summary triggers warning but does not fail passed
    df_short_summary = clean_df.copy()
    df_short_summary.loc[0, "summary_chars"] = 5  # Below threshold 30
    report = run_data_quality_checks(df_short_summary, test_settings, "test_short_summary")
    assert report["passed"] is True  # still passes hard checks
    assert report["warning_checks"]["summary_chars_below_minimum"]["triggered"] is True
    assert report["summary"]["triggered_warnings"] == 1

    # Test stale row triggers warning but does not fail passed
    df_stale = clean_df.copy()
    df_stale.loc[0, "age_days"] = 200  # Stale (> freshness threshold 180)
    report = run_data_quality_checks(df_stale, test_settings, "test_stale")
    assert report["passed"] is True
    assert report["warning_checks"]["stale_rows"]["triggered"] is True
    assert report["summary"]["triggered_warnings"] == 1


def test_run_data_quality_checks_saves_json(clean_df, test_settings):
    report_name = "test_save_report"
    report = run_data_quality_checks(clean_df, test_settings, report_name)
    
    expected_path = test_settings.paths.quality_dir / f"{report_name}.json"
    assert expected_path.exists()


def test_build_freshness_report(clean_df, test_settings):
    # Test freshness report structure on clean/fresh data
    report_path = test_settings.paths.freshness_report
    report = build_freshness_report(clean_df, test_settings, report_path)
    
    assert isinstance(report, dict)
    assert report["latest_published"] == "2026-06-02"
    assert report["oldest_published"] == "2026-06-01"
    assert report["stale_rows"] == 0
    assert report["total_rows"] == 2
    assert report["freshness_threshold_days"] == test_settings.freshness_threshold_days
    assert report["is_fresh"] is True
    assert report_path.exists()

    # Test freshness report still marks stale data as not fresh
    df_stale = clean_df.copy()
    df_stale.loc[0, "age_days"] = 200  # Stale
    report_stale = build_freshness_report(df_stale, test_settings, report_path)
    assert report_stale["is_fresh"] is False
    assert report_stale["stale_rows"] == 1


def test_quality_reports_run_id(clean_df, test_settings):
    report_name = "test_run_id_report"
    run_id = "test_run"
    report = run_data_quality_checks(clean_df, test_settings, report_name, run_id=run_id)
    
    assert "run_id" in report
    assert "created_at" in report
    assert report["run_id"] == run_id
    
    from core.utils import read_json
    expected_path = test_settings.paths.quality_dir / f"{report_name}.json"
    assert expected_path.exists()
    saved_report = read_json(expected_path)
    assert saved_report["run_id"] == run_id
    
    report_path = test_settings.paths.freshness_report
    f_report = build_freshness_report(clean_df, test_settings, report_path, run_id=run_id)
    
    assert "run_id" in f_report
    assert f_report["run_id"] == run_id
    
    assert report_path.exists()
    saved_f_report = read_json(report_path)
    assert saved_f_report["run_id"] == run_id

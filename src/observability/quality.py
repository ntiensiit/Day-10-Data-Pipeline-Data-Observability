from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from core.config import Settings
from core.utils import write_json, now_utc


def _utc_timestamp() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def run_data_quality_checks(
    df: pd.DataFrame,
    settings: Settings,
    report_name: str,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run a suite of data quality checks on the papers DataFrame and save the JSON report."""
    total_rows = len(df)
    
    # Initialize hard checks dict
    hard_checks = {}
    
    # 1. Check row count greater than zero
    passed_row_count = total_rows > 0
    hard_checks["row_count_above_zero"] = {
        "passed": passed_row_count,
        "observed": total_rows,
    }

    # 2. Check paper_id column exists
    paper_id_exists = "paper_id" in df.columns
    hard_checks["paper_id_column_exists"] = {
        "passed": paper_id_exists,
        "observed": paper_id_exists,
    }

    # 3. Check paper_id has no null/empty values
    if paper_id_exists:
        null_count = df["paper_id"].isna().sum() + (df["paper_id"] == "").sum()
        hard_checks["paper_id_has_no_nulls"] = {
            "passed": int(null_count) == 0,
            "observed": int(null_count),
        }
    else:
        hard_checks["paper_id_has_no_nulls"] = {"passed": False, "observed": None}

    # 4. Check paper_id is unique
    if paper_id_exists:
        dup_count = df["paper_id"].duplicated().sum()
        hard_checks["paper_id_is_unique"] = {
            "passed": int(dup_count) == 0,
            "observed": int(dup_count),
        }
    else:
        hard_checks["paper_id_is_unique"] = {"passed": False, "observed": None}

    # 5. Check title column exists
    title_exists = "title" in df.columns
    hard_checks["title_column_exists"] = {
        "passed": title_exists,
        "observed": title_exists,
    }

    # 6. Check title has no null/empty values
    if title_exists:
        null_count = df["title"].isna().sum() + (df["title"] == "").sum()
        hard_checks["title_has_no_nulls"] = {
            "passed": int(null_count) == 0,
            "observed": int(null_count),
        }
    else:
        hard_checks["title_has_no_nulls"] = {"passed": False, "observed": None}

    # 7. Check summary column exists
    summary_exists = "summary" in df.columns
    hard_checks["summary_column_exists"] = {
        "passed": summary_exists,
        "observed": summary_exists,
    }

    # 8. Check summary has no null/empty values
    if summary_exists:
        null_count = df["summary"].isna().sum() + (df["summary"] == "").sum()
        hard_checks["summary_has_no_nulls"] = {
            "passed": int(null_count) == 0,
            "observed": int(null_count),
        }
    else:
        hard_checks["summary_has_no_nulls"] = {"passed": False, "observed": None}

    # 9. Check text_for_embedding column exists
    text_for_embedding_exists = "text_for_embedding" in df.columns
    hard_checks["text_for_embedding_exists"] = {
        "passed": text_for_embedding_exists,
        "observed": text_for_embedding_exists,
    }

    # 10. Check text_for_embedding has no null/empty values
    if text_for_embedding_exists:
        null_count = df["text_for_embedding"].isna().sum() + (df["text_for_embedding"] == "").sum()
        hard_checks["text_for_embedding_has_no_nulls"] = {
            "passed": int(null_count) == 0,
            "observed": int(null_count),
        }
    else:
        hard_checks["text_for_embedding_has_no_nulls"] = {"passed": False, "observed": None}

    # 11. Check age_days column exists
    age_days_exists = "age_days" in df.columns
    hard_checks["age_days_column_exists"] = {
        "passed": age_days_exists,
        "observed": age_days_exists,
    }

    # Initialize warning checks dict
    warning_checks = {}

    # 1. Stale rows detected by freshness_threshold_days
    if age_days_exists and total_rows > 0:
        stale_count = int((df["age_days"] > settings.freshness_threshold_days).sum())
        warning_checks["stale_rows"] = {
            "triggered": stale_count > 0,
            "observed": stale_count,
            "threshold": settings.freshness_threshold_days,
            "message": f"{stale_count} rows are older than the freshness threshold."
        }
    else:
        warning_checks["stale_rows"] = {
            "triggered": False,
            "observed": 0,
            "threshold": settings.freshness_threshold_days,
            "message": "0 rows are older than the freshness threshold."
        }

    # 2. summary_chars below minimum
    min_summary_chars = 30
    if "summary_chars" in df.columns and total_rows > 0:
        below_min = int((df["summary_chars"] < min_summary_chars).sum())
        warning_checks["summary_chars_below_minimum"] = {
            "triggered": below_min > 0,
            "observed": below_min,
            "threshold": min_summary_chars,
            "message": f"{below_min} rows have summary characters below minimum."
        }
    else:
        warning_checks["summary_chars_below_minimum"] = {
            "triggered": False,
            "observed": 0,
            "threshold": min_summary_chars,
            "message": "0 rows have summary characters below minimum."
        }

    # 3. Missing authors_joined
    if "authors_joined" in df.columns and total_rows > 0:
        missing_authors = int((df["authors_joined"].isna() | (df["authors_joined"] == "")).sum())
        warning_checks["missing_authors_joined"] = {
            "triggered": missing_authors > 0,
            "observed": missing_authors,
            "threshold": 0,
            "message": f"{missing_authors} rows are missing authors_joined."
        }
    else:
        warning_checks["missing_authors_joined"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 0,
            "message": "0 rows are missing authors_joined."
        }

    # 4. Missing categories_joined
    if "categories_joined" in df.columns and total_rows > 0:
        missing_categories = int((df["categories_joined"].isna() | (df["categories_joined"] == "")).sum())
        warning_checks["missing_categories_joined"] = {
            "triggered": missing_categories > 0,
            "observed": missing_categories,
            "threshold": 0,
            "message": f"{missing_categories} rows are missing categories_joined."
        }
    else:
        warning_checks["missing_categories_joined"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 0,
            "message": "0 rows are missing categories_joined."
        }

    # 5. Missing abs_url
    if "abs_url" in df.columns and total_rows > 0:
        missing_abs = int((df["abs_url"].isna() | (df["abs_url"] == "")).sum())
        warning_checks["missing_abs_url"] = {
            "triggered": missing_abs > 0,
            "observed": missing_abs,
            "threshold": 0,
            "message": f"{missing_abs} rows are missing abs_url."
        }
    else:
        warning_checks["missing_abs_url"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 0,
            "message": "0 rows are missing abs_url."
        }

    # 6. Missing pdf_url
    if "pdf_url" in df.columns and total_rows > 0:
        missing_pdf = int((df["pdf_url"].isna() | (df["pdf_url"] == "")).sum())
        warning_checks["missing_pdf_url"] = {
            "triggered": missing_pdf > 0,
            "observed": missing_pdf,
            "threshold": 0,
            "message": f"{missing_pdf} rows are missing pdf_url."
        }
    else:
        warning_checks["missing_pdf_url"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 0,
            "message": "0 rows are missing pdf_url."
        }

    # 7. Future published dates
    if "age_days" in df.columns and total_rows > 0:
        future_dates = int((df["age_days"] < 0).sum())
        warning_checks["future_published_dates"] = {
            "triggered": future_dates > 0,
            "observed": future_dates,
            "threshold": 0,
            "message": f"{future_dates} rows have future published dates."
        }
    else:
        warning_checks["future_published_dates"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 0,
            "message": "0 rows have future published dates."
        }

    # 8. Very short title
    if "title" in df.columns and total_rows > 0:
        short_titles = int((df["title"].apply(lambda t: len(str(t)) < 5)).sum())
        warning_checks["very_short_title"] = {
            "triggered": short_titles > 0,
            "observed": short_titles,
            "threshold": 5,
            "message": f"{short_titles} rows have a very short title."
        }
    else:
        warning_checks["very_short_title"] = {
            "triggered": False,
            "observed": 0,
            "threshold": 5,
            "message": "0 rows have a very short title."
        }

    # 9. Very long or very short text_for_embedding
    if "text_for_embedding" in df.columns and total_rows > 0:
        bad_embedding_texts = int((df["text_for_embedding"].apply(lambda t: len(str(t)) < 50 or len(str(t)) > 10000)).sum())
        warning_checks["very_long_or_short_text_for_embedding"] = {
            "triggered": bad_embedding_texts > 0,
            "observed": bad_embedding_texts,
            "threshold": [50, 10000],
            "message": f"{bad_embedding_texts} rows have very long or short text for embedding."
        }
    else:
        warning_checks["very_long_or_short_text_for_embedding"] = {
            "triggered": False,
            "observed": 0,
            "threshold": [50, 10000],
            "message": "0 rows have very long or short text for embedding."
        }

    # Calculate overall passed status based only on hard checks
    passed = all(chk["passed"] for chk in hard_checks.values())

    # Calculate summary counts
    passed_hard_checks = sum(1 for chk in hard_checks.values() if chk["passed"])
    failed_hard_checks = sum(1 for chk in hard_checks.values() if not chk["passed"])
    triggered_warnings = sum(1 for chk in warning_checks.values() if chk["triggered"])

    summary = {
        "total_hard_checks": len(hard_checks),
        "passed_hard_checks": passed_hard_checks,
        "failed_hard_checks": failed_hard_checks,
        "total_warning_checks": len(warning_checks),
        "triggered_warnings": triggered_warnings,
    }

    # Backward compatible flat checks dictionary
    checks = {}
    for k, v in hard_checks.items():
        checks[k] = v
    summary_chars_exists = "summary_chars" in df.columns
    checks["summary_chars_column_exists"] = {
        "passed": summary_chars_exists,
        "observed": summary_chars_exists,
    }
    checks["summary_chars_above_minimum"] = {
        "passed": not warning_checks["summary_chars_below_minimum"]["triggered"] if summary_chars_exists else False,
        "observed": warning_checks["summary_chars_below_minimum"]["observed"],
    }
    checks["no_stale_rows"] = {
        "passed": not warning_checks["stale_rows"]["triggered"] if "age_days" in df.columns else False,
        "observed": warning_checks["stale_rows"]["observed"],
    }
    summary["total_checks"] = len(checks)
    summary["passed_checks"] = sum(1 for chk in checks.values() if chk["passed"])
    summary["failed_checks"] = sum(1 for chk in checks.values() if not chk["passed"])

    report = {
        "report_name": report_name,
        "run_id": run_id,
        "created_at": _utc_timestamp(),
        "passed": passed,
        "summary": summary,
        "hard_checks": hard_checks,
        "warning_checks": warning_checks,
        "checks": checks,
        "checks_note": "Legacy checks are kept for backward compatibility. Use hard_checks and warning_checks for pass/fail interpretation.",
    }

    report_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_path, report)
    return report


def build_freshness_report(
    df: pd.DataFrame,
    settings: Settings,
    report_path: Path,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Compile and write freshness report containing min/max dates, stale row count, and freshness status."""
    total_rows = len(df)
    if df.empty:
        latest_published = ""
        oldest_published = ""
        stale_rows = 0
        is_fresh = False
    else:
        if "published" in df.columns:
            published_values = pd.to_datetime(df["published"], errors="coerce")
            valid_published = published_values.dropna()
            latest_published = valid_published.max().strftime("%Y-%m-%d") if not valid_published.empty else ""
            oldest_published = valid_published.min().strftime("%Y-%m-%d") if not valid_published.empty else ""
        else:
            latest_published = ""
            oldest_published = ""
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else 0
        is_fresh = stale_rows == 0

    report = {
        "run_id": run_id,
        "created_at": _utc_timestamp(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    write_json(Path(report_path), report)
    return report

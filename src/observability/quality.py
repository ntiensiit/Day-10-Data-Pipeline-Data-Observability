from __future__ import annotations

from pathlib import Path
from typing import Any
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run a suite of data quality checks on the papers DataFrame and save the JSON report."""
    checks = {}
    total_rows = len(df)

    # 1. Check row count greater than zero
    passed_row_count = total_rows > 0
    checks["row_count_above_zero"] = {
        "passed": passed_row_count,
        "observed": total_rows,
    }

    # 2. Check paper_id column exists
    paper_id_exists = "paper_id" in df.columns
    checks["paper_id_column_exists"] = {
        "passed": paper_id_exists,
        "observed": paper_id_exists,
    }

    # 3. Check paper_id has no null/empty values
    paper_id_no_nulls = False
    if paper_id_exists:
        null_count = df["paper_id"].isna().sum() + (df["paper_id"] == "").sum()
        paper_id_no_nulls = int(null_count) == 0
        checks["paper_id_has_no_nulls"] = {
            "passed": paper_id_no_nulls,
            "observed": int(null_count),
        }
    else:
        checks["paper_id_has_no_nulls"] = {"passed": False, "observed": None}

    # 4. Check paper_id is unique
    paper_id_unique = False
    if paper_id_exists:
        dup_count = df["paper_id"].duplicated().sum()
        paper_id_unique = int(dup_count) == 0
        checks["paper_id_is_unique"] = {
            "passed": paper_id_unique,
            "observed": int(dup_count),
        }
    else:
        checks["paper_id_is_unique"] = {"passed": False, "observed": None}

    # 5. Check title column exists
    title_exists = "title" in df.columns
    checks["title_column_exists"] = {
        "passed": title_exists,
        "observed": title_exists,
    }

    # 6. Check title has no null/empty values
    title_no_nulls = False
    if title_exists:
        null_count = df["title"].isna().sum() + (df["title"] == "").sum()
        title_no_nulls = int(null_count) == 0
        checks["title_has_no_nulls"] = {
            "passed": title_no_nulls,
            "observed": int(null_count),
        }
    else:
        checks["title_has_no_nulls"] = {"passed": False, "observed": None}

    # 7. Check summary column exists
    summary_exists = "summary" in df.columns
    checks["summary_column_exists"] = {
        "passed": summary_exists,
        "observed": summary_exists,
    }

    # 8. Check summary has no null/empty values
    summary_no_nulls = False
    if summary_exists:
        null_count = df["summary"].isna().sum() + (df["summary"] == "").sum()
        summary_no_nulls = int(null_count) == 0
        checks["summary_has_no_nulls"] = {
            "passed": summary_no_nulls,
            "observed": int(null_count),
        }
    else:
        checks["summary_has_no_nulls"] = {"passed": False, "observed": None}

    # 9. Check text_for_embedding column exists
    text_for_embedding_exists = "text_for_embedding" in df.columns
    checks["text_for_embedding_exists"] = {
        "passed": text_for_embedding_exists,
        "observed": text_for_embedding_exists,
    }

    # 10. Check text_for_embedding has no null/empty values
    text_for_embedding_no_nulls = False
    if text_for_embedding_exists:
        null_count = df["text_for_embedding"].isna().sum() + (df["text_for_embedding"] == "").sum()
        text_for_embedding_no_nulls = int(null_count) == 0
        checks["text_for_embedding_has_no_nulls"] = {
            "passed": text_for_embedding_no_nulls,
            "observed": int(null_count),
        }
    else:
        checks["text_for_embedding_has_no_nulls"] = {"passed": False, "observed": None}

    # 11. Check summary_chars column exists
    summary_chars_exists = "summary_chars" in df.columns
    checks["summary_chars_column_exists"] = {
        "passed": summary_chars_exists,
        "observed": summary_chars_exists,
    }

    # 12. Check summary_chars is above a reasonable minimum
    summary_chars_above_min = False
    min_summary_chars = 30
    if summary_chars_exists and total_rows > 0:
        below_min = (df["summary_chars"] < min_summary_chars).sum()
        summary_chars_above_min = int(below_min) == 0
        checks["summary_chars_above_minimum"] = {
            "passed": summary_chars_above_min,
            "observed": int(below_min),
        }
    else:
        checks["summary_chars_above_minimum"] = {"passed": False, "observed": None}

    # 13. Check age_days column exists
    age_days_exists = "age_days" in df.columns
    checks["age_days_column_exists"] = {
        "passed": age_days_exists,
        "observed": age_days_exists,
    }

    # 14. Detect stale rows using settings.freshness_threshold_days
    no_stale_rows = False
    if age_days_exists and total_rows > 0:
        stale_count = (df["age_days"] > settings.freshness_threshold_days).sum()
        no_stale_rows = int(stale_count) == 0
        checks["no_stale_rows"] = {
            "passed": no_stale_rows,
            "observed": int(stale_count),
        }
    else:
        checks["no_stale_rows"] = {"passed": False, "observed": None}

    # Calculate overall passed status
    passed = all(chk["passed"] for chk in checks.values())

    summary = {
        "total_checks": len(checks),
        "passed_checks": sum(1 for chk in checks.values() if chk["passed"]),
        "failed_checks": sum(1 for chk in checks.values() if not chk["passed"]),
    }

    report = {
        "report_name": report_name,
        "passed": passed,
        "summary": summary,
        "checks": checks,
    }

    report_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(report_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
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
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    write_json(Path(report_path), report)
    return report

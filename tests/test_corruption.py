from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from ingestion.corruption import corrupt_clean_dataframe
from core.utils import read_json


@pytest.fixture
def sample_clean_df():
    # Create a DataFrame with 8 rows to trigger all corruption branches (requiring len > 4 after dropping 2)
    rows = []
    for i in range(8):
        rows.append({
            "paper_id": f"10.1000/paper_{i}",
            "title": f"Title of Paper {i}",
            "summary": f"This is the summary of paper number {i}.",
            "authors_joined": f"Author {i}",
            "categories_joined": "CS",
            "abs_url": f"http://example.com/{i}",
            "pdf_url": f"http://example.com/{i}.pdf",
            "published": f"2026-06-0{i+1}",
            "updated": f"2026-06-0{i+1}",
            "age_days": 10 - i,
            "summary_chars": len(f"This is the summary of paper number {i}."),
            "text_for_embedding": f"Title of Paper {i}"
        })
    return pd.DataFrame(rows)


def test_corrupt_clean_dataframe(sample_clean_df, tmp_path):
    log_path = tmp_path / "corruption_log.json"
    run_id = "test_run_123"
    
    df_corrupted = corrupt_clean_dataframe(sample_clean_df, log_path, run_id=run_id)

    # Test output is not empty
    assert not df_corrupted.empty

    # Test corrupted output has fewer rows after dropping latest records, then duplicate row is added
    # Input: 8 rows. Drops 2 -> 6 rows. Duplicate added -> 7 rows.
    assert len(df_corrupted) == 7

    # Load corruption log to inspect IDs
    assert log_path.exists()
    log = read_json(log_path)
    assert log["run_id"] == run_id
    assert "created_at" in log
    assert not log["created_at"].endswith("+00:00Z")

    # Test corruption log includes required fields
    required_log_keys = [
        "dropped_ids", "blanked_ids", "noise_ids",
        "truncated_ids", "stale_ids", "duplicate_ids"
    ]
    for key in required_log_keys:
        assert key in log

    # Test at least one summary is blank
    blanked_id = log["blanked_ids"][0]
    blanked_row = df_corrupted[df_corrupted["paper_id"] == blanked_id]
    assert blanked_row.iloc[0]["summary"] == ""

    # Test at least one summary contains corruption noise
    noise_id = log["noise_ids"][0]
    noise_row = df_corrupted[df_corrupted["paper_id"] == noise_id]
    assert " [CORRUPTED NOISE_TEXT_FLAG]" in noise_row.iloc[0]["summary"]

    # Test at least one title is truncated
    truncated_id = log["truncated_ids"][0]
    truncated_row = df_corrupted[df_corrupted["paper_id"] == truncated_id]
    assert len(truncated_row.iloc[0]["title"]) == 3

    # Test at least one published value is stale
    stale_id = log["stale_ids"][0]
    stale_row = df_corrupted[df_corrupted["paper_id"] == stale_id]
    assert stale_row.iloc[0]["published"] == "2010-01-01"

    # Test duplicate paper_id exists
    dup_id = log["duplicate_ids"][0]
    dup_rows = df_corrupted[df_corrupted["paper_id"] == dup_id]
    assert len(dup_rows) == 2

    # Test summary_chars is recomputed
    for idx, row in df_corrupted.iterrows():
        assert row["summary_chars"] == len(str(row["summary"]))

    # Test text_for_embedding is recomputed
    for idx, row in df_corrupted.iterrows():
        text = row["text_for_embedding"]
        assert row["title"] in text
        assert row["summary"] in text

    # Test age_days is recomputed using current date
    # (Since it's recomputed using datetime.now(UTC), we check that it is non-negative / exists)
    assert "age_days" in df_corrupted.columns
    assert (df_corrupted["age_days"] >= 0).all()


def test_corruption_is_deterministic(sample_clean_df, tmp_path):
    log_path1 = tmp_path / "log1.json"
    log_path2 = tmp_path / "log2.json"
    
    df_c1 = corrupt_clean_dataframe(sample_clean_df, log_path1, run_id="run1")
    df_c2 = corrupt_clean_dataframe(sample_clean_df, log_path2, run_id="run1")

    pd.testing.assert_frame_equal(df_c1, df_c2)

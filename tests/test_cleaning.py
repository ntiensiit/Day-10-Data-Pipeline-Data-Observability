from __future__ import annotations

from datetime import datetime, UTC
import pandas as pd
import pytest

from ingestion.crossref import PaperRecord
from ingestion.cleaning import build_clean_dataframe


def test_build_clean_dataframe():
    # Create sample PaperRecord with valid fields
    record1 = PaperRecord(
        paper_id="10.1000/xyz123",
        title="Test Title NFC \u00e9",  # é in NFC
        summary="Test summary content.  With   multiple   spaces.",
        authors=["Author One", "Author Two"],
        categories=["Computer Science", "Artificial Intelligence"],
        primary_category="Computer Science",
        published="2026-06-01T12:00:00Z",
        updated="2026-06-02T12:00:00Z",
        abs_url="http://example.com/abs",
        pdf_url="http://example.com/pdf",
        comment="A comment",
    )

    run_date = datetime(2026, 6, 10, tzinfo=UTC)
    df = build_clean_dataframe([record1], run_date)

    # Test build_clean_dataframe() returns non-empty DataFrame
    assert not df.empty
    assert len(df) == 1

    # Test output includes required columns
    expected_cols = [
        "paper_id", "title", "summary", "authors", "authors_joined",
        "categories", "categories_joined", "primary_category",
        "published", "updated", "abs_url", "pdf_url", "comment",
        "age_days", "summary_chars", "text_for_embedding"
    ]
    for col in expected_cols:
        assert col in df.columns

    # Test whitespace normalization
    assert df.loc[0, "summary"] == "Test summary content. With multiple spaces."

    # Test Unicode NFC normalization
    # "\u00e9" is already NFC, let's check it is properly preserved/normalized
    assert df.loc[0, "title"] == "Test Title NFC \u00e9"

    # Test published is converted to YYYY-MM-DD
    assert df.loc[0, "published"] == "2026-06-01"

    # Test updated is converted to YYYY-MM-DD
    assert df.loc[0, "updated"] == "2026-06-02"

    # Test age_days is computed correctly from run_date
    # 2026-06-10 - 2026-06-01 = 9 days
    assert df.loc[0, "age_days"] == 9

    # Test authors_joined joins authors with comma
    assert df.loc[0, "authors_joined"] == "Author One, Author Two"

    # Test categories_joined joins categories with comma
    assert df.loc[0, "categories_joined"] == "Computer Science, Artificial Intelligence"

    # Test summary_chars equals summary length
    assert df.loc[0, "summary_chars"] == len(df.loc[0, "summary"])

    # Test text_for_embedding contains title, summary, authors, categories, published date, URL, PDF URL
    text_for_embedding = df.loc[0, "text_for_embedding"]
    assert "Test Title NFC \u00e9" in text_for_embedding
    assert "Test summary content. With multiple spaces." in text_for_embedding
    assert "Author One, Author Two" in text_for_embedding
    assert "Computer Science, Artificial Intelligence" in text_for_embedding
    assert "2026-06-01" in text_for_embedding
    assert "http://example.com/abs" in text_for_embedding
    assert "http://example.com/pdf" in text_for_embedding


def test_build_clean_dataframe_drops_invalid():
    run_date = datetime(2026, 6, 10, tzinfo=UTC)

    # Missing paper_id
    rec_no_id = PaperRecord(
        paper_id="",
        title="Title",
        summary="Summary",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-01",
        updated="",
        abs_url="",
        pdf_url="",
        comment="",
    )

    # Missing title
    rec_no_title = PaperRecord(
        paper_id="id123",
        title="",
        summary="Summary",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-01",
        updated="",
        abs_url="",
        pdf_url="",
        comment="",
    )

    # Missing summary
    rec_no_summary = PaperRecord(
        paper_id="id456",
        title="Title",
        summary="",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-01",
        updated="",
        abs_url="",
        pdf_url="",
        comment="",
    )

    df = build_clean_dataframe([rec_no_id, rec_no_title, rec_no_summary], run_date)
    assert df.empty


def test_build_clean_dataframe_deduplication_and_sorting():
    run_date = datetime(2026, 6, 10, tzinfo=UTC)

    # Duplicate paper_id, different published dates (should pick the first after sorting)
    rec1 = PaperRecord(
        paper_id="dup_id",
        title="First Title",
        summary="Summary one",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-01",
        updated="2026-06-01",
        abs_url="",
        pdf_url="",
        comment="",
    )

    rec2 = PaperRecord(
        paper_id="dup_id",
        title="Second Title (Later)",
        summary="Summary two",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-03",
        updated="2026-06-03",
        abs_url="",
        pdf_url="",
        comment="",
    )

    # Deterministic sorting check
    rec3 = PaperRecord(
        paper_id="abc_id",
        title="ABC Title",
        summary="ABC Summary",
        authors=[],
        categories=[],
        primary_category="",
        published="2026-06-01",
        updated="",
        abs_url="",
        pdf_url="",
        comment="",
    )

    df = build_clean_dataframe([rec1, rec2, rec3], run_date)
    assert len(df) == 2

    # Duplicate paper_id rows are deduplicated
    # Under build_clean_dataframe, the sorting is by:
    # ["_published_sort", "_updated_sort", "paper_id"] descending for dates, keeping first.
    # So "Second Title (Later)" with published date 2026-06-03 should be kept!
    dup_row = df[df["paper_id"] == "dup_id"]
    assert len(dup_row) == 1
    assert dup_row.iloc[0]["title"] == "Second Title (Later)"

    # Test output sorting is deterministic by paper_id ascending
    assert df.iloc[0]["paper_id"] == "abc_id"
    assert df.iloc[1]["paper_id"] == "dup_id"

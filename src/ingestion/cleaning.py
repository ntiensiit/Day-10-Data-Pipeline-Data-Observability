from __future__ import annotations

from datetime import datetime
import re
import unicodedata
import pandas as pd

from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a structured, normalized DataFrame ready for embedding index building."""
    if not records:
        cols = [
            "paper_id", "title", "summary", "authors", "authors_joined",
            "categories", "categories_joined", "primary_category",
            "published", "updated", "abs_url", "pdf_url", "comment",
            "age_days", "summary_chars", "text_for_embedding"
        ]
        return pd.DataFrame(columns=cols)

    def normalize_text(text: str | None) -> str:
        if text is None:
            return ""
        s = str(text)
        normalized = unicodedata.normalize("NFC", s)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def normalize_list(lst: list[str] | None) -> list[str]:
        if not lst or not isinstance(lst, list):
            return []
        return [normalize_text(item) for item in lst if item]

    cleaned_rows = []
    for r in records:
        paper_id = normalize_text(r.paper_id)
        title = normalize_text(r.title)
        summary = normalize_text(r.summary)

        # Drop invalid/empty critical fields before putting in dataframe
        if not paper_id or not title or not summary:
            continue

        authors = normalize_list(r.authors)
        authors_joined = ", ".join(authors)

        categories = normalize_list(r.categories)
        categories_joined = ", ".join(categories)
        primary_category = normalize_text(r.primary_category)
        if not primary_category and categories:
            primary_category = categories[0]

        # Ensure published and updated dates are parsed/formatted
        published = normalize_text(r.published)
        updated = normalize_text(r.updated)

        def clean_date_str(d_str: str) -> str:
            if not d_str:
                return ""
            dt = pd.to_datetime(d_str, errors="coerce")
            if pd.isna(dt):
                return ""
            return dt.strftime("%Y-%m-%d")

        published = clean_date_str(published)
        updated = clean_date_str(updated)
        if not updated:
            updated = published

        abs_url = normalize_text(r.abs_url)
        pdf_url = normalize_text(r.pdf_url)
        comment = normalize_text(r.comment)

        cleaned_rows.append({
            "paper_id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "authors_joined": authors_joined,
            "categories": categories,
            "categories_joined": categories_joined,
            "primary_category": primary_category,
            "published": published,
            "updated": updated,
            "abs_url": abs_url,
            "pdf_url": pdf_url,
            "comment": comment,
        })

    if not cleaned_rows:
        cols = [
            "paper_id", "title", "summary", "authors", "authors_joined",
            "categories", "categories_joined", "primary_category",
            "published", "updated", "abs_url", "pdf_url", "comment",
            "age_days", "summary_chars", "text_for_embedding"
        ]
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(cleaned_rows)

    # Convert dates for age_days calculation
    run_date_only = pd.to_datetime(run_date).date()
    
    def calc_age(pub_str: str) -> int:
        if not pub_str:
            return 999999
        try:
            pub_date = pd.to_datetime(pub_str).date()
            return (run_date_only - pub_date).days
        except Exception:
            return 999999

    df["age_days"] = df["published"].apply(calc_age)
    df["summary_chars"] = df["summary"].apply(lambda s: len(s) if isinstance(s, str) else 0)

    # Ensure text_for_embedding includes title, summary, authors, categories, published date, and URLs
    def make_embedding_text(row: pd.Series) -> str:
        return (
            f"Title: {row['title']}\n"
            f"Summary: {row['summary']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Published: {row['published']}\n"
            f"URL: {row['abs_url']}\n"
            f"PDF: {row['pdf_url']}"
        )

    df["text_for_embedding"] = df.apply(make_embedding_text, axis=1)

    # Drop duplicates by paper_id, keeping the latest stable record deterministically.
    df["_published_sort"] = pd.to_datetime(df["published"], errors="coerce")
    df["_updated_sort"] = pd.to_datetime(df["updated"], errors="coerce")
    df = df.sort_values(
        by=["_published_sort", "_updated_sort", "paper_id"],
        ascending=[False, False, True],
        kind="mergesort",
    )
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.drop(columns=["_published_sort", "_updated_sort"])

    # Sort output deterministically
    df = df.sort_values(by=["paper_id"], ascending=True, kind="mergesort")
    df = df.reset_index(drop=True)

    return df

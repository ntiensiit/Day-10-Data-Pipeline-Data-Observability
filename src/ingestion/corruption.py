from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(
    df: pd.DataFrame,
    output_log_path: Path,
    run_id: str | None = None,
) -> pd.DataFrame:
    """Simulate data corruption on the cleaned DataFrame and write the details to a log file."""
    # 1. Copy the input DataFrame
    df_corrupt = df.copy()

    # 2. Drop a few latest records
    # Sort by published date descending and drop the top 2 records deterministically
    df_sorted = df_corrupt.sort_values(by=["published", "paper_id"], ascending=[False, True], kind="mergesort")
    dropped_ids = list(df_sorted["paper_id"].head(2))
    df_corrupt = df_sorted.iloc[2:].copy()
    df_corrupt = df_corrupt.reset_index(drop=True)

    blanked_ids = []
    noise_ids = []
    truncated_ids = []
    stale_ids = []
    duplicate_ids = []

    # 3. Blank summary for some rows
    if len(df_corrupt) > 0:
        row_id = df_corrupt.loc[0, "paper_id"]
        df_corrupt.loc[0, "summary"] = ""
        blanked_ids.append(row_id)

    # 4. Inject noise into summary
    if len(df_corrupt) > 1:
        row_id = df_corrupt.loc[1, "paper_id"]
        df_corrupt.loc[1, "summary"] = df_corrupt.loc[1, "summary"] + " [CORRUPTED NOISE_TEXT_FLAG]"
        noise_ids.append(row_id)

    # 5. Truncate title for some rows
    if len(df_corrupt) > 2:
        row_id = df_corrupt.loc[2, "paper_id"]
        df_corrupt.loc[2, "title"] = df_corrupt.loc[2, "title"][:3]
        truncated_ids.append(row_id)

    # 6. Make some published dates stale
    if len(df_corrupt) > 3:
        row_id = df_corrupt.loc[3, "paper_id"]
        df_corrupt.loc[3, "published"] = "2010-01-01"
        stale_ids.append(row_id)

    # 7. Add duplicate rows
    if len(df_corrupt) > 4:
        dup_row = df_corrupt.iloc[[4]]
        df_corrupt = pd.concat([df_corrupt, dup_row], ignore_index=True)
        duplicate_ids.append(df_corrupt.iloc[4]["paper_id"])

    # 8. Recompute summary_chars, text_for_embedding, age_days
    df_corrupt["summary_chars"] = df_corrupt["summary"].apply(lambda s: len(s) if isinstance(s, str) else 0)

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

    df_corrupt["text_for_embedding"] = df_corrupt.apply(make_embedding_text, axis=1)

    run_date_only = datetime.now(UTC).date()

    def calc_age(pub_str: str) -> int:
        if not pub_str:
            return 999999
        try:
            pub_date = pd.to_datetime(pub_str).date()
            return (run_date_only - pub_date).days
        except Exception:
            return 999999

    df_corrupt["age_days"] = df_corrupt["published"].apply(calc_age)

    # 9. Write corruption log JSON
    log = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dropped_ids": dropped_ids,
        "blanked_ids": blanked_ids,
        "noise_ids": noise_ids,
        "truncated_ids": truncated_ids,
        "stale_ids": stale_ids,
        "duplicate_ids": duplicate_ids,
    }
    write_json(Path(output_log_path), log)

    return df_corrupt

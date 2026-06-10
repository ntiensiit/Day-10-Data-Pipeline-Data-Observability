from __future__ import annotations

from typing import Any
from pathlib import Path
import pandas as pd

from core.utils import write_json, first_sentence


def build_test_set(df: pd.DataFrame, output_path: Path) -> list[dict[str, Any]]:
    """Build a deterministic evaluation test set from the cleaned papers DataFrame."""
    if df.empty:
        write_json(output_path, [])
        return []

    # Sort deterministically by paper_id and pick top 5 papers
    sorted_df = df.sort_values(by="paper_id").reset_index(drop=True)
    num_papers = min(len(sorted_df), 5)

    test_set: list[dict[str, Any]] = []
    idx = 0

    for i in range(num_papers):
        row = sorted_df.iloc[i]
        title = row["title"]
        paper_id = row["paper_id"]

        # 1. Summary question (not matching special keywords, falls back to summary)
        test_set.append({
            "id": f"eval_q_{idx}",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{title}'?",
            "ground_truth": first_sentence(row["summary"]),
            "ground_truth_doc_ids": [paper_id],
        })
        idx += 1

        # 2. Authors question (matches 'who authored')
        test_set.append({
            "id": f"eval_q_{idx}",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": row["authors_joined"],
            "ground_truth_doc_ids": [paper_id],
        })
        idx += 1

        # 3. Date question (matches 'when was')
        test_set.append({
            "id": f"eval_q_{idx}",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": row["published"],
            "ground_truth_doc_ids": [paper_id],
        })
        idx += 1

        # 4. Categories question (matches 'what categories')
        test_set.append({
            "id": f"eval_q_{idx}",
            "question_type": "categories",
            "question": f"What categories does the paper '{title}' belong to?",
            "ground_truth": row["categories_joined"],
            "ground_truth_doc_ids": [paper_id],
        })
        idx += 1

    # Write test set to output JSON path
    write_json(output_path, test_set)
    return test_set

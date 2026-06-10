from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from evaluation.testset import build_test_set
from core.utils import read_json


@pytest.fixture
def sample_clean_df():
    return pd.DataFrame([
        {
            "paper_id": "10.1000/paper_a",
            "title": "Agentic RAG and LLMs",
            "summary": "This paper discusses agentic retrieval augmented generation using large language models. We present a novel framework.",
            "authors_joined": "John Doe, Jane Smith",
            "categories_joined": "Computer Science, AI",
            "published": "2026-06-01",
        },
        {
            "paper_id": "10.1000/paper_b",
            "title": "Observability in Data Pipelines",
            "summary": "Data observability is key to robust production pipelines. We introduce telemetry tools.",
            "authors_joined": "Alice Johnson",
            "categories_joined": "Software Engineering",
            "published": "2026-06-02",
        }
    ])


def test_build_test_set_basic(sample_clean_df, tmp_path):
    output_path = tmp_path / "test_set.json"
    test_set = build_test_set(sample_clean_df, output_path)

    # Test output is a list
    assert isinstance(test_set, list)
    
    # Test JSON test set file is written
    assert output_path.exists()
    loaded_set = read_json(output_path)
    assert len(loaded_set) == len(test_set)

    # Output has 4 questions per paper (summary, authors, date, categories)
    # 2 papers -> 8 items
    assert len(test_set) == 8

    # Test each item has: id, question_type, question, ground_truth, ground_truth_doc_ids
    required_keys = ["id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"]
    for item in test_set:
        for key in required_keys:
            assert key in item

    # Test question types include: summary, authors, date, categories
    question_types = {item["question_type"] for item in test_set}
    assert question_types == {"summary", "authors", "date", "categories"}

    # Test exact paper title appears in questions and ground_truth_doc_ids contains correct paper_id
    paper_titles = list(sample_clean_df["title"])
    paper_ids = list(sample_clean_df["paper_id"])
    
    for item in test_set:
        # Check if the title is in the question
        title_matched = False
        for title in paper_titles:
            if title in item["question"]:
                title_matched = True
                break
        assert title_matched

        # Check doc ID matches
        doc_ids = item["ground_truth_doc_ids"]
        assert len(doc_ids) == 1
        assert doc_ids[0] in paper_ids


def test_build_test_set_deterministic(sample_clean_df, tmp_path):
    output_path1 = tmp_path / "test_set1.json"
    output_path2 = tmp_path / "test_set2.json"

    set1 = build_test_set(sample_clean_df, output_path1)
    set2 = build_test_set(sample_clean_df, output_path2)

    # Test output is deterministic
    assert set1 == set2


def test_build_test_set_empty_df(tmp_path):
    output_path = tmp_path / "empty_test_set.json"
    empty_df = pd.DataFrame()

    test_set = build_test_set(empty_df, output_path)

    # Test empty DataFrame writes empty list
    assert test_set == []
    assert output_path.exists()
    assert read_json(output_path) == []

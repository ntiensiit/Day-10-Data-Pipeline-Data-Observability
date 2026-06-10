from __future__ import annotations

import pandas as pd
from pathlib import Path

from core.config import load_settings
from core.utils import read_json, write_csv, write_json, now_utc
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe

import pandas as pd
from pathlib import Path

from core.config import load_settings
from core.utils import read_json, write_csv, write_json, now_utc
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_corruption_report


def main() -> None:
    """Run the corruption simulation, evaluate the degraded pipeline, repair the dataset, and report comparisons."""
    # 1. Load settings
    settings = load_settings()
    run_date = now_utc()
    run_id = run_date.strftime("%Y%m%dT%H%M%SZ")

    # 2. Check whether baseline cleaned data and metrics exist
    clean_exists = settings.paths.clean_csv.exists() and settings.paths.clean_json.exists()
    testset_exists = settings.paths.eval_testset.exists()
    metrics_exists = settings.paths.baseline_metrics.exists()
    raw_exists = settings.paths.raw_api_response.exists() and settings.paths.raw_records_json.exists()

    # 3. If baseline artifacts are missing, run phase1 first
    if not clean_exists or not metrics_exists or not testset_exists or not raw_exists:
        print("Baseline artifacts are missing. Running phase1 baseline flow first...")
        from pipelines.phase1 import main as run_phase1
        run_phase1()

    # 4. Load baseline cleaned dataset
    print("Loading baseline cleaned dataset...")
    df_clean = pd.read_csv(settings.paths.clean_csv)
    if df_clean.empty:
        raise RuntimeError("Baseline cleaned dataset is empty. Run phase1 and verify the cleaned corpus before corruption flow.")

    # 5. Create corrupted dataset using corrupt_clean_dataframe
    print("Creating corrupted dataset...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log, run_id=run_id)
    if df_corrupted.empty:
        raise RuntimeError("Corrupted dataset is empty. Check the baseline cleaned data before building embeddings.")

    # 6. Save corrupted CSV and JSON
    print(f"Saving corrupted papers to {settings.paths.corrupted_clean_csv}...")
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))

    # 7. Build corrupted Chroma index
    print("Building corrupted Chroma index...")
    corrupted_index = LocalEmbeddingIndex.build(
        df_corrupted, settings, settings.paths.corrupted_embeddings_json
    )

    # 8. Evaluate corrupted pipeline using existing test set
    print("Evaluating corrupted pipeline performance...")
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # 9. Run corrupted quality checks and freshness report
    print("Running data quality checks on corrupted dataset...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted_quality", run_id=run_id)

    print("Building freshness report for corrupted dataset...")
    corrupted_freshness = build_freshness_report(
        df_corrupted, settings, settings.paths.quality_dir / "corrupted_freshness_report.json", run_id=run_id
    )

    # 10. Rebuild repaired cleaned data from raw records
    print("Rebuilding/repairing dataset from raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, now_utc())
    if df_repaired.empty:
        raise RuntimeError("Repaired dataset is empty. Check Crossref source query, filter, or parsing rules.")

    # 11. Save repaired CSV and JSON
    print(f"Saving repaired papers to {settings.paths.repaired_clean_csv}...")
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))

    # 12. Build repaired Chroma index
    print("Building repaired Chroma index...")
    repaired_index = LocalEmbeddingIndex.build(
        df_repaired, settings, settings.paths.repaired_embeddings_json
    )

    # 13. Evaluate repaired pipeline
    print("Evaluating repaired pipeline performance...")
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    # 14. Run repaired quality checks and freshness report
    print("Running data quality checks on repaired dataset...")
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired_quality", run_id=run_id)

    print("Building freshness report for repaired dataset...")
    repaired_freshness = build_freshness_report(
        df_repaired, settings, settings.paths.quality_dir / "repaired_freshness_report.json", run_id=run_id
    )

    # 15. Load baseline metrics for comparison report
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # 16. Generate corruption comparison Markdown report
    print(f"Generating corruption comparison report at {settings.paths.comparison_report}...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_eval.summary,
        repaired_metrics=repaired_eval.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        run_id=run_id,
    )

    print("Corruption flow pipeline successfully completed!")

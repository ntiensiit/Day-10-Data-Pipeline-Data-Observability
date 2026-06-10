from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report


def main() -> None:
    """Run the end-to-end baseline data pipeline: fetch raw records, clean, index, evaluate, and report."""
    # 1. Load settings
    settings = load_settings()
    run_date = now_utc()
    run_id = run_date.strftime("%Y%m%dT%H%M%SZ")

    # 2. Load or fetch raw records
    raw_exists = settings.paths.raw_records_json.exists() and settings.paths.raw_api_response.exists()

    if settings.refresh_source or not raw_exists:
        print("Fetching raw records from Crossref API...")
        records = fetch_source_records(settings)
    else:
        print("Loading existing raw records from disk...")
        records = load_raw_records(settings.paths.raw_records_json)

    # 3. Build cleaned DataFrame
    print("Building cleaned DataFrame...")
    df = build_clean_dataframe(records, run_date)
    if df.empty:
        raise RuntimeError("Cleaned dataset is empty. Check Crossref source query, filter, or parsing rules.")

    # 4. Save cleaned CSV and JSON
    print(f"Saving cleaned papers to {settings.paths.clean_csv}...")
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    # 5. Build Chroma index
    print("Building local embedding index...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json, run_id=run_id)

    # 6. Build evaluation test set if missing
    test_set_path = settings.paths.eval_testset
    if settings.refresh_source or settings.refresh_test_set or not test_set_path.exists():
        print("Generating evaluation test set...")
        build_test_set(df, test_set_path)
    else:
        print("Using existing evaluation test set...")

    # 7. Evaluate baseline pipeline
    print("Evaluating baseline pipeline performance...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=test_set_path,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
        run_id=run_id,
    )

    # 8. Run data quality checks and build freshness report
    print("Running data quality checks...")
    quality_report = run_data_quality_checks(df, settings, "baseline_quality", run_id=run_id)

    print("Building freshness report...")
    freshness_rep = build_freshness_report(df, settings, settings.paths.freshness_report, run_id=run_id)

    # 9. Generate baseline Markdown report
    print(f"Generating Phase 1 report at {settings.paths.baseline_report}...")
    source_summary = {
        "run_id": run_id,
        "created_at": run_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "max_results": settings.max_results,
        "total_records": len(records),
    }

    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_rep,
    )

    print("Phase 1 baseline pipeline successfully completed!")

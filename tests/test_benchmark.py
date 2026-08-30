from __future__ import annotations

import json

from healthcare_sorting.benchmark import (
    create_charts,
    run_benchmarks,
    summarize_results,
    write_environment_file,
    write_result_files,
)
from healthcare_sorting.data import load_healthcare_records


def test_benchmark_runs_every_requested_combination(healthcare_csv):
    records, _ = load_healthcare_records(healthcare_csv)

    results = run_benchmarks(
        records,
        sizes=[10, 20],
        runs=2,
        seed=412,
        measure_memory=False,
    )

    assert len(results) == 2 * 2 * 4 * 3
    assert {result.algorithm for result in results} == {"merge", "heap", "quick", "python"}
    assert {result.input_order for result in results} == {"sorted", "random", "reverse"}
    assert all(result.time_ms >= 0 for result in results)


def test_benchmark_rejects_oversized_sample(healthcare_csv):
    records, _ = load_healthcare_records(healthcare_csv)

    try:
        run_benchmarks(records, sizes=[31], runs=1, seed=412)
    except ValueError as error:
        assert "exceeds the dataset" in str(error)
    else:
        raise AssertionError("oversized sample should fail")


def test_result_artifacts_are_created(healthcare_csv, tmp_path):
    records, _ = load_healthcare_records(healthcare_csv)
    results = run_benchmarks(
        records,
        sizes=[10],
        runs=1,
        seed=412,
        algorithms=["merge", "quick"],
        input_orders=["random"],
        measure_memory=False,
    )

    raw_path, summary_path, summaries = write_result_files(results, tmp_path)
    runtime_path, memory_path = create_charts(summaries, tmp_path)
    environment_path = write_environment_file(
        tmp_path,
        dataset_path=healthcare_csv,
        record_count=len(records),
        sizes=[10],
        runs=1,
        seed=412,
    )

    assert raw_path.read_text(encoding="utf-8").startswith("algorithm,input_order")
    assert summary_path.exists()
    assert runtime_path.stat().st_size > 0
    assert memory_path.stat().st_size > 0
    assert json.loads(environment_path.read_text(encoding="utf-8"))["dataset"]["records"] == 30
    assert len(summarize_results(results)) == 2

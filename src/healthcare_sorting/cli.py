"""Command-line interface for sorting CSV files and running benchmarks."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from healthcare_sorting.algorithms import heap_sort, merge_sort, quick_sort
from healthcare_sorting.benchmark import (
    ALGORITHMS,
    INPUT_ORDERS,
    create_charts,
    run_benchmarks,
    write_environment_file,
    write_result_files,
)
from healthcare_sorting.data import load_csv_records, load_healthcare_records, write_csv_records

DEFAULT_SIZES = (1_000, 5_000, 10_000, 25_000, 50_000)


def _sort_records(records: list[dict[str, Any]], algorithm: str, key_name: str) -> None:
    def key(record: dict[str, Any]) -> Any:
        return record[key_name]

    if algorithm == "merge":
        merge_sort(records, key=key)
    elif algorithm == "heap":
        heap_sort(records, key=key)
    elif algorithm == "quick":
        quick_sort(records, key=key)
    else:
        records.sort(key=key)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="healthcare-sorting",
        description="Sort CSV records or benchmark sorting algorithms.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sort_parser = subparsers.add_parser("sort", help="sort a CSV file")
    sort_parser.add_argument("--algorithm", choices=ALGORITHMS, required=True)
    sort_parser.add_argument("--input", type=Path, required=True)
    sort_parser.add_argument("--output", type=Path, required=True)
    sort_parser.add_argument("--key", default="Date of Admission")

    benchmark_parser = subparsers.add_parser("benchmark", help="run reproducible benchmarks")
    benchmark_parser.add_argument(
        "--data", type=Path, default=Path("data/healthcare_dataset.csv")
    )
    benchmark_parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_SIZES))
    benchmark_parser.add_argument("--runs", type=int, default=5)
    benchmark_parser.add_argument("--seed", type=int, default=412)
    benchmark_parser.add_argument("--output-dir", type=Path, default=Path("results"))
    benchmark_parser.add_argument(
        "--algorithms", nargs="+", choices=ALGORITHMS, default=list(ALGORITHMS)
    )
    benchmark_parser.add_argument(
        "--input-orders", nargs="+", choices=INPUT_ORDERS, default=list(INPUT_ORDERS)
    )
    benchmark_parser.add_argument(
        "--skip-memory",
        action="store_true",
        help="skip the separate tracemalloc pass (useful for quick smoke tests)",
    )
    return parser


def _run_sort(arguments: argparse.Namespace) -> int:
    if arguments.input.resolve() == arguments.output.resolve():
        raise ValueError("input and output paths must be different")
    records, columns = load_csv_records(arguments.input, arguments.key)
    _sort_records(records, arguments.algorithm, arguments.key)
    write_csv_records(records, columns, arguments.output)
    print(f"Sorted {len(records):,} records with {arguments.algorithm} sort.")
    print(f"Output: {arguments.output}")
    return 0


def _run_benchmark(arguments: argparse.Namespace) -> int:
    records, _ = load_healthcare_records(arguments.data)
    results = run_benchmarks(
        records,
        sizes=arguments.sizes,
        runs=arguments.runs,
        seed=arguments.seed,
        algorithms=arguments.algorithms,
        input_orders=arguments.input_orders,
        measure_memory=not arguments.skip_memory,
    )
    raw_path, summary_path, summaries = write_result_files(results, arguments.output_dir)
    runtime_path, memory_path = create_charts(summaries, arguments.output_dir)
    environment_path = write_environment_file(
        arguments.output_dir,
        dataset_path=arguments.data,
        record_count=len(records),
        sizes=arguments.sizes,
        runs=arguments.runs,
        seed=arguments.seed,
    )

    print(f"Completed {len(results):,} benchmark trials.")
    for path in (raw_path, summary_path, runtime_path, memory_path, environment_path):
        print(f"Output: {path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "sort":
            return _run_sort(arguments)
        return _run_benchmark(arguments)
    except (FileNotFoundError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def entrypoint() -> None:
    raise SystemExit(main())

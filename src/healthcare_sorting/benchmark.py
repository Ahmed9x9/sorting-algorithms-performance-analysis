"""Reproducible runtime and memory benchmarks for the sorting algorithms."""

from __future__ import annotations

import csv
import gc
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

from healthcare_sorting.algorithms import heap_sort, merge_sort, quick_sort

Record = dict[str, Any]
RecordSorter = Callable[[list[Record], Callable[[Record], Any]], None]


def _python_sort(items: list[Record], key: Callable[[Record], Any]) -> None:
    items.sort(key=key)


ALGORITHMS: dict[str, RecordSorter] = {
    "merge": merge_sort,
    "heap": heap_sort,
    "quick": quick_sort,
    "python": _python_sort,
}
INPUT_ORDERS = ("sorted", "random", "reverse")


@dataclass(frozen=True)
class BenchmarkResult:
    """One timed and memory-profiled benchmark trial."""

    algorithm: str
    input_order: str
    size: int
    run: int
    seed: int
    time_ms: float
    peak_memory_kib: float


def _validate_result(
    original: Sequence[Record], candidate: Sequence[Record], key: Callable[[Record], Any]
) -> None:
    if len(original) != len(candidate):
        raise RuntimeError("sorting algorithm changed the number of records")
    if Counter(map(id, original)) != Counter(map(id, candidate)):
        raise RuntimeError("sorting algorithm did not preserve the input records")
    out_of_order = any(
        key(candidate[index]) > key(candidate[index + 1])
        for index in range(len(candidate) - 1)
    )
    if out_of_order:
        raise RuntimeError("sorting algorithm returned records in the wrong order")


def _make_trial_input(
    sorted_records: Sequence[Record], input_order: str, trial_seed: int
) -> list[Record]:
    if input_order == "sorted":
        return list(sorted_records)
    if input_order == "reverse":
        return list(reversed(sorted_records))
    if input_order == "random":
        randomized = list(sorted_records)
        random.Random(trial_seed).shuffle(randomized)
        return randomized
    raise ValueError(f"unsupported input order: {input_order}")


def _measure_peak_memory(
    sorter: RecordSorter,
    source: Sequence[Record],
    key: Callable[[Record], Any],
) -> tuple[list[Record], float]:
    candidate = list(source)
    gc.collect()
    tracemalloc.start()
    try:
        sorter(candidate, key)
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return candidate, peak_bytes / 1024


def run_benchmarks(
    records: Sequence[Record],
    *,
    key_name: str = "Date of Admission",
    sizes: Iterable[int],
    runs: int,
    seed: int,
    algorithms: Iterable[str] = ALGORITHMS,
    input_orders: Iterable[str] = INPUT_ORDERS,
    measure_memory: bool = True,
) -> list[BenchmarkResult]:
    """Run fair trials using the same source order for every algorithm."""

    requested_sizes = tuple(sizes)
    requested_algorithms = tuple(algorithms)
    requested_orders = tuple(input_orders)

    if not requested_sizes or any(size <= 0 for size in requested_sizes):
        raise ValueError("benchmark sizes must be positive integers")
    if max(requested_sizes) > len(records):
        raise ValueError(
            f"largest benchmark size ({max(requested_sizes)}) exceeds "
            f"the dataset ({len(records)})"
        )
    if runs <= 0:
        raise ValueError("runs must be a positive integer")

    unknown_algorithms = set(requested_algorithms) - ALGORITHMS.keys()
    if unknown_algorithms:
        raise ValueError(f"unknown algorithms: {', '.join(sorted(unknown_algorithms))}")
    unknown_orders = set(requested_orders) - set(INPUT_ORDERS)
    if unknown_orders:
        raise ValueError(f"unknown input orders: {', '.join(sorted(unknown_orders))}")

    def key(record: Record) -> Any:
        return record[key_name]

    results: list[BenchmarkResult] = []

    for size in requested_sizes:
        sample = list(records[:size])
        sorted_records = sorted(sample, key=key)

        for run_number in range(1, runs + 1):
            trial_seed = seed + size * 100 + run_number

            for input_order in requested_orders:
                source = _make_trial_input(sorted_records, input_order, trial_seed)

                for algorithm in requested_algorithms:
                    sorter = ALGORITHMS[algorithm]
                    candidate = list(source)

                    start = time.perf_counter_ns()
                    sorter(candidate, key)
                    elapsed_ns = time.perf_counter_ns() - start
                    _validate_result(source, candidate, key)

                    peak_memory_kib = 0.0
                    if measure_memory:
                        memory_candidate, peak_memory_kib = _measure_peak_memory(
                            sorter, source, key
                        )
                        _validate_result(source, memory_candidate, key)

                    results.append(
                        BenchmarkResult(
                            algorithm=algorithm,
                            input_order=input_order,
                            size=size,
                            run=run_number,
                            seed=trial_seed,
                            time_ms=elapsed_ns / 1_000_000,
                            peak_memory_kib=peak_memory_kib,
                        )
                    )

    return results


def summarize_results(results: Sequence[BenchmarkResult]) -> list[dict[str, Any]]:
    """Aggregate trials by algorithm, input order, and input size."""

    groups: dict[tuple[str, str, int], list[BenchmarkResult]] = defaultdict(list)
    for result in results:
        groups[(result.algorithm, result.input_order, result.size)].append(result)

    summaries: list[dict[str, Any]] = []
    for (algorithm, input_order, size), trials in sorted(groups.items()):
        timings = [trial.time_ms for trial in trials]
        memory = [trial.peak_memory_kib for trial in trials]
        summaries.append(
            {
                "algorithm": algorithm,
                "input_order": input_order,
                "size": size,
                "runs": len(trials),
                "mean_ms": round(statistics.fmean(timings), 6),
                "median_ms": round(statistics.median(timings), 6),
                "stdev_ms": round(statistics.stdev(timings), 6) if len(timings) > 1 else 0.0,
                "mean_peak_memory_kib": round(statistics.fmean(memory), 3),
                "max_peak_memory_kib": round(max(memory), 3),
            }
        )
    return summaries


def _write_csv(path: Path, rows: Sequence[dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_result_files(
    results: Sequence[BenchmarkResult], output_directory: str | Path
) -> tuple[Path, Path, list[dict[str, Any]]]:
    """Write raw trials and aggregated statistics as CSV files."""

    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    raw_path = output_path / "raw_timings.csv"
    summary_path = output_path / "summary.csv"
    raw_rows = [asdict(result) for result in results]
    summaries = summarize_results(results)

    _write_csv(raw_path, raw_rows, tuple(BenchmarkResult.__dataclass_fields__))
    _write_csv(summary_path, summaries, tuple(summaries[0]) if summaries else ())
    return raw_path, summary_path, summaries


def write_environment_file(
    output_directory: str | Path,
    *,
    dataset_path: str | Path,
    record_count: int,
    sizes: Sequence[int],
    runs: int,
    seed: int,
) -> Path:
    """Record enough environment and input metadata to interpret a result snapshot."""

    data_path = Path(dataset_path)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "dependencies": {
            "matplotlib": version("matplotlib"),
            "pandas": version("pandas"),
        },
        "dataset": {
            "path": data_path.as_posix(),
            "records": record_count,
            "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        },
        "benchmark": {"sizes": list(sizes), "runs": runs, "seed": seed},
    }
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    environment_path = output_path / "environment.json"
    environment_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return environment_path


def create_charts(
    summaries: Sequence[dict[str, Any]], output_directory: str | Path
) -> tuple[Path, Path]:
    """Create runtime and peak-memory charts from summary rows."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    runtime_path = output_path / "runtime.png"
    memory_path = output_path / "memory.png"

    algorithm_names = [
        name for name in ALGORITHMS if any(row["algorithm"] == name for row in summaries)
    ]
    order_names = [
        name for name in INPUT_ORDERS if any(row["input_order"] == name for row in summaries)
    ]

    def draw(
        metric: str,
        ylabel: str,
        title: str,
        destination: Path,
        *,
        logarithmic: bool = False,
    ) -> None:
        use_logarithmic_scale = logarithmic and any(
            float(row[metric]) > 0 for row in summaries
        )
        figure, axes = plt.subplots(1, len(order_names), figsize=(15, 4.5), sharey=True)
        if len(order_names) == 1:
            axes = [axes]

        for axis, input_order in zip(axes, order_names, strict=True):
            for algorithm in algorithm_names:
                rows = sorted(
                    (
                        row
                        for row in summaries
                        if row["algorithm"] == algorithm and row["input_order"] == input_order
                    ),
                    key=lambda row: int(row["size"]),
                )
                axis.plot(
                    [int(row["size"]) for row in rows],
                    [float(row[metric]) for row in rows],
                    marker="o",
                    linewidth=2,
                    label=algorithm.title() if algorithm != "python" else "Python Timsort",
                )
            axis.set_title(f"{input_order.title()} input")
            axis.set_xlabel("Records")
            axis.grid(alpha=0.3)
            if use_logarithmic_scale:
                axis.set_yscale("log")

        axes[0].set_ylabel(ylabel)
        handles, labels = axes[-1].get_legend_handles_labels()
        figure.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.93),
            ncol=len(labels),
            frameon=True,
        )
        figure.suptitle(title, y=0.99)
        figure.tight_layout(rect=(0, 0, 1, 0.84))
        figure.savefig(destination, dpi=160, bbox_inches="tight")
        plt.close(figure)

    draw("mean_ms", "Mean runtime (ms)", "Sorting runtime by input order", runtime_path)
    draw(
        "mean_peak_memory_kib",
        "Mean peak allocation (KiB, log scale)",
        "Auxiliary Python allocation by input order",
        memory_path,
        logarithmic=True,
    )
    return runtime_path, memory_path

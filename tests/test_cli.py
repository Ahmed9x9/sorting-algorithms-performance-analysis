from __future__ import annotations

import pandas as pd

from healthcare_sorting.cli import main


def test_sort_command_writes_sorted_csv(healthcare_csv, tmp_path):
    destination = tmp_path / "sorted.csv"

    exit_code = main(
        [
            "sort",
            "--algorithm",
            "quick",
            "--input",
            str(healthcare_csv),
            "--output",
            str(destination),
        ]
    )

    frame = pd.read_csv(destination)
    dates = pd.to_datetime(frame["Date of Admission"])
    assert exit_code == 0
    assert dates.is_monotonic_increasing


def test_sort_command_rejects_same_input_and_output(healthcare_csv):
    exit_code = main(
        [
            "sort",
            "--algorithm",
            "merge",
            "--input",
            str(healthcare_csv),
            "--output",
            str(healthcare_csv),
        ]
    )

    assert exit_code == 2


def test_benchmark_command_creates_outputs(healthcare_csv, tmp_path):
    output_directory = tmp_path / "results"

    exit_code = main(
        [
            "benchmark",
            "--data",
            str(healthcare_csv),
            "--sizes",
            "10",
            "--runs",
            "1",
            "--algorithms",
            "merge",
            "quick",
            "--input-orders",
            "random",
            "--skip-memory",
            "--output-dir",
            str(output_directory),
        ]
    )

    assert exit_code == 0
    assert (output_directory / "summary.csv").exists()
    assert (output_directory / "runtime.png").exists()

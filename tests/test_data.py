from __future__ import annotations

import pandas as pd
import pytest

from healthcare_sorting.data import load_csv_records, load_healthcare_records, write_csv_records


def test_load_healthcare_records_validates_and_parses_dates(healthcare_csv):
    records, columns = load_healthcare_records(healthcare_csv)

    assert len(records) == 30
    assert columns[0] == "Name"
    assert str(records[0]["Date of Admission"].date()) == "2020-01-01"


def test_load_csv_records_rejects_unknown_key(healthcare_csv):
    with pytest.raises(ValueError, match="sort key"):
        load_csv_records(healthcare_csv, "Unknown")


def test_healthcare_schema_rejects_missing_columns(tmp_path):
    path = tmp_path / "incomplete.csv"
    pd.DataFrame([{"Name": "Example", "Date of Admission": "2024-01-01"}]).to_csv(
        path, index=False
    )

    with pytest.raises(ValueError, match="missing columns"):
        load_healthcare_records(path)


def test_write_csv_records_preserves_column_order(healthcare_csv, tmp_path):
    records, columns = load_csv_records(healthcare_csv, "Date of Admission")
    destination = tmp_path / "nested" / "output.csv"

    write_csv_records(records, columns, destination)

    assert list(pd.read_csv(destination).columns) == columns

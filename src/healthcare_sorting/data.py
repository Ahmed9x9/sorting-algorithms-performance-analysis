"""CSV loading, validation, and writing helpers."""

from pathlib import Path
from typing import Any

import pandas as pd

DATE_COLUMNS = {"Date of Admission", "Discharge Date"}
REQUIRED_HEALTHCARE_COLUMNS = (
    "Name",
    "Age",
    "Gender",
    "Blood Type",
    "Medical Condition",
    "Date of Admission",
    "Doctor",
    "Hospital",
    "Insurance Provider",
    "Billing Amount",
    "Room Number",
    "Admission Type",
    "Discharge Date",
    "Medication",
    "Test Results",
)


def load_csv_records(path: str | Path, key: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Load CSV records and parse a date-like sort key when necessary."""

    csv_path = Path(path)
    frame = pd.read_csv(csv_path)
    if key not in frame.columns:
        raise ValueError(f"sort key {key!r} is not present in {csv_path}")

    if key in DATE_COLUMNS or "date" in key.casefold():
        frame[key] = pd.to_datetime(frame[key], errors="raise")
        if frame[key].isna().any():
            raise ValueError(f"sort key {key!r} contains missing dates")

    return frame.to_dict(orient="records"), list(frame.columns)


def load_healthcare_records(
    path: str | Path, key: str = "Date of Admission"
) -> tuple[list[dict[str, Any]], list[str]]:
    """Load records after validating the canonical healthcare schema."""

    csv_path = Path(path)
    header = pd.read_csv(csv_path, nrows=0)
    missing = [column for column in REQUIRED_HEALTHCARE_COLUMNS if column not in header.columns]
    if missing:
        raise ValueError(f"healthcare dataset is missing columns: {', '.join(missing)}")
    return load_csv_records(csv_path, key)


def write_csv_records(
    records: list[dict[str, Any]], columns: list[str], output_path: str | Path
) -> None:
    """Write records to CSV while retaining the source column order."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame.from_records(records, columns=columns).to_csv(destination, index=False)

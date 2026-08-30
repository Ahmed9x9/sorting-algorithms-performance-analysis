from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from healthcare_sorting.data import REQUIRED_HEALTHCARE_COLUMNS


@pytest.fixture
def healthcare_csv(tmp_path):
    rows = []
    start = date(2020, 1, 1)
    for index in range(30):
        rows.append(
            {
                "Name": f"Patient {index}",
                "Age": 20 + index % 60,
                "Gender": "Female" if index % 2 else "Male",
                "Blood Type": "A+",
                "Medical Condition": "Asthma",
                "Date of Admission": (start + timedelta(days=(index * 7) % 19)).isoformat(),
                "Doctor": "Dr. Example",
                "Hospital": "Example Hospital",
                "Insurance Provider": "Aetna",
                "Billing Amount": 1000 + index,
                "Room Number": 100 + index,
                "Admission Type": "Urgent",
                "Discharge Date": (start + timedelta(days=(index * 7) % 19 + 2)).isoformat(),
                "Medication": "Aspirin",
                "Test Results": "Normal",
            }
        )

    path = tmp_path / "healthcare.csv"
    pd.DataFrame(rows, columns=REQUIRED_HEALTHCARE_COLUMNS).to_csv(path, index=False)
    return path

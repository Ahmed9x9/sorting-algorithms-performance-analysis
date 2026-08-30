from __future__ import annotations

import random

import pytest

from healthcare_sorting import heap_sort, merge_sort, quick_sort

ALGORITHMS = (merge_sort, heap_sort, quick_sort)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [4, 1, 4, 2, 1, 4, 3],
        [0, -5, 10, -1, 3],
    ],
)
def test_algorithms_match_builtin_sorted(algorithm, values):
    candidate = list(values)

    result = algorithm(candidate)

    assert result is None
    assert candidate == sorted(values)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_algorithms_support_record_keys(algorithm):
    records = [
        {"name": "third", "priority": 3},
        {"name": "first", "priority": 1},
        {"name": "second", "priority": 2},
    ]

    algorithm(records, key=lambda record: record["priority"])

    assert [record["priority"] for record in records] == [1, 2, 3]


def test_merge_sort_is_stable():
    records = [
        {"id": "a", "key": 2},
        {"id": "b", "key": 1},
        {"id": "c", "key": 2},
        {"id": "d", "key": 1},
    ]

    merge_sort(records, key=lambda record: record["key"])

    assert [record["id"] for record in records] == ["b", "d", "a", "c"]


@pytest.mark.parametrize(
    "values",
    [
        list(range(5_000)),
        list(range(5_000, 0, -1)),
        [7] * 5_000,
    ],
)
def test_quick_sort_handles_inputs_larger_than_recursion_limit(values):
    quick_sort(values)
    assert values == sorted(values)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_randomized_inputs_match_builtin(algorithm):
    randomizer = random.Random(412)
    values = [randomizer.randrange(-100, 101) for _ in range(1_000)]
    expected = sorted(values)

    algorithm(values)

    assert values == expected

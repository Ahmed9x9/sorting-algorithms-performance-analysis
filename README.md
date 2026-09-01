# Sorting Algorithms Performance Analysis - 2024-2025, 1st Term

How much does the order of the input affect a sorting algorithm?

This project compares Merge Sort, Heap Sort, and Quick Sort by running them on the same
55,500 synthetic healthcare records. Python's built-in Timsort is included as a reference so the
hand-written algorithms can also be compared with the sort people would normally use in Python.

![Runtime comparison](results/runtime.png)

## About the project

This started as a group project for an Algorithm Analysis and Design course during the first
term of the 2024-2025 academic year. I later reorganized the code, fixed the benchmarking process,
added tests, and made the experiments reproducible.

The healthcare dataset is only being used as a realistic collection of records to sort. It was
generated with Faker and does not contain real patient information.

## Algorithms

| Algorithm | Best time | Average time | Worst time | Extra space | Stable |
|---|---:|---:|---:|---:|:---:|
| Merge Sort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(n)` | Yes |
| Heap Sort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(1)` | No |
| Quick Sort | `O(n log n)` | `O(n log n)` | `O(n^2)` | `O(log n)` stack | No |
| Python Timsort | `O(n)` | `O(n log n)` | `O(n log n)` | `O(n)` | Yes |

Quick Sort uses a median-of-three pivot, three-way partitioning, and an explicit stack. The
three-way partition is useful here because many records share the same admission date. The
explicit stack also prevents the recursion errors that a basic recursive implementation can hit
with large or already sorted inputs.

## Running the project

Create a virtual environment and install the project:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

Sort the dataset by admission date:

```bash
python -m healthcare_sorting sort \
  --algorithm quick \
  --input data/healthcare_dataset.csv \
  --output outputs/healthcare_sorted.csv \
  --key "Date of Admission"
```

Run the full benchmark:

```bash
python -m healthcare_sorting benchmark \
  --data data/healthcare_dataset.csv \
  --sizes 1000 5000 10000 25000 50000 \
  --runs 5 \
  --seed 412 \
  --output-dir results
```

The installed `healthcare-sorting` command provides the same `sort` and `benchmark` commands.
Use `--help` to see the available options.

## How the benchmark works

I used five input sizes: 1,000, 5,000, 10,000, 25,000, and 50,000 records. Each test was repeated
five times with sorted, randomly shuffled, and reverse-sorted input.

To keep the comparison fair:

- Every algorithm receives the same records in the same order.
- A new list is created before each run so one algorithm cannot affect the next one.
- Random input uses a fixed seed, so the same test can be reproduced.
- CSV loading and result validation are not included in the recorded sorting time.
- Runtime is measured with `time.perf_counter_ns()`.
- Memory is measured in a separate pass with `tracemalloc`, so it does not affect the runtime.
- Every output is checked to make sure it is sorted and contains all the original records.

The words `sorted`, `random`, and `reverse` describe the input order. They are not labeled best,
average, and worst because those cases are different for each algorithm.

The saved benchmark contains 300 trials. The individual runs are in
[`results/raw_timings.csv`](results/raw_timings.csv), the averages are in
[`results/summary.csv`](results/summary.csv), and details about the machine and Python environment
are in [`results/environment.json`](results/environment.json).

## Results

These were the average times for 50,000 records:

| Algorithm | Sorted | Random | Reverse |
|---|---:|---:|---:|
| Merge Sort | 175.38 ms | 253.21 ms | **172.97 ms** |
| Heap Sort | 311.98 ms | 418.15 ms | 350.83 ms |
| Quick Sort | **161.72 ms** | **219.18 ms** | 215.36 ms |
| Python Timsort | 17.54 ms | 42.56 ms | 25.44 ms |

The bold numbers show the fastest of the three hand-written algorithms. Quick Sort was fastest on
sorted and random input, while Merge Sort was fastest on reverse-sorted input. Heap Sort was the
slowest in these tests, but it used the least extra memory. Python's built-in sort was much faster
than all three, which is expected from an optimized library implementation.

Merge Sort used about 392 KiB of extra Python-managed memory at 50,000 records. Heap Sort and
Quick Sort both stayed below 2 KiB during the traced sorting step.

![Memory comparison](results/memory.png)

Results will vary between computers, so the main value is in the overall pattern rather than a
single timing number.

## Repository layout

```text
src/healthcare_sorting/   Sorting algorithms, benchmark code, and command-line interface
tests/                    Algorithm and command-line tests
data/                     Synthetic dataset and its license information
results/                  Benchmark tables, charts, and environment details
.github/workflows/        Automated tests for Python 3.10 and 3.12
```

## Dataset

The project uses the [Healthcare Dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset),
which is released under CC0. A copy is included so the benchmark works without a Kaggle account.
More information and the file checksum are available in [`data/README.md`](data/README.md).

## Limitations

The algorithms are written in pure Python and were tested on one synthetic dataset and one
computer. The results should not be treated as a general ranking for every possible workload.
Also, `tracemalloc` measures Python-managed allocations rather than the total memory used by the
process.

## License

The source code is available under the [MIT License](LICENSE). The dataset is available separately
under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

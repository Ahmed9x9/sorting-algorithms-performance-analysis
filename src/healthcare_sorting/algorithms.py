"""Generic, hand-written sorting algorithms used by the benchmark."""

from collections.abc import Callable, MutableSequence
from typing import Any, TypeVar

T = TypeVar("T")
KeyFunction = Callable[[T], Any]


def _identity(value: T) -> T:
    return value


def merge_sort(items: MutableSequence[T], key: KeyFunction[T] | None = None) -> None:
    """Sort *items* in place with stable Merge Sort.

    Time complexity is O(n log n) in every case and auxiliary space is O(n).
    """

    key_function = key or _identity
    auxiliary = list(items)

    def sort_range(start: int, end: int) -> None:
        if end - start < 2:
            return

        middle = (start + end) // 2
        sort_range(start, middle)
        sort_range(middle, end)

        for index in range(start, end):
            auxiliary[index] = items[index]

        left = start
        right = middle
        destination = start

        while left < middle and right < end:
            if key_function(auxiliary[left]) <= key_function(auxiliary[right]):
                items[destination] = auxiliary[left]
                left += 1
            else:
                items[destination] = auxiliary[right]
                right += 1
            destination += 1

        while left < middle:
            items[destination] = auxiliary[left]
            left += 1
            destination += 1

        while right < end:
            items[destination] = auxiliary[right]
            right += 1
            destination += 1

    sort_range(0, len(items))


def heap_sort(items: MutableSequence[T], key: KeyFunction[T] | None = None) -> None:
    """Sort *items* in place with Heap Sort.

    Time complexity is O(n log n) and auxiliary space is O(1).
    """

    key_function = key or _identity
    length = len(items)

    def sift_down(root: int, heap_size: int) -> None:
        while True:
            largest = root
            left = 2 * root + 1
            right = left + 1

            if left < heap_size and key_function(items[largest]) < key_function(items[left]):
                largest = left
            if right < heap_size and key_function(items[largest]) < key_function(items[right]):
                largest = right
            if largest == root:
                return

            items[root], items[largest] = items[largest], items[root]
            root = largest

    for root in range(length // 2 - 1, -1, -1):
        sift_down(root, length)

    for end in range(length - 1, 0, -1):
        items[0], items[end] = items[end], items[0]
        sift_down(0, end)


def _median_of_three_index(
    items: MutableSequence[T], first: int, middle: int, last: int, key: KeyFunction[T]
) -> int:
    first_key = key(items[first])
    middle_key = key(items[middle])
    last_key = key(items[last])

    if first_key < middle_key:
        if middle_key < last_key:
            return middle
        return last if first_key < last_key else first

    if first_key < last_key:
        return first
    return last if middle_key < last_key else middle


def quick_sort(items: MutableSequence[T], key: KeyFunction[T] | None = None) -> None:
    """Sort *items* in place with an iterative three-way Quick Sort.

    Median-of-three pivot selection behaves well for ordered data, while the
    three-way partition prevents repeated keys from producing deep partitions.
    Only the larger partition is stacked, keeping stack use bounded by O(log n).
    The worst-case running time remains O(n squared).
    """

    if len(items) < 2:
        return

    key_function = key or _identity
    stack = [(0, len(items) - 1)]

    while stack:
        low, high = stack.pop()

        while low < high:
            middle = (low + high) // 2
            pivot_index = _median_of_three_index(items, low, middle, high, key_function)
            pivot_key = key_function(items[pivot_index])

            # First collect values below the pivot. Unlike the usual Dutch-flag
            # loop, this pass does not reverse a sorted greater-than partition.
            lower = low
            for current in range(low, high + 1):
                if key_function(items[current]) < pivot_key:
                    items[lower], items[current] = items[current], items[lower]
                    lower += 1

            # Values at or above the pivot remain. Move keys equal to the pivot
            # directly after the lower partition, leaving greater keys at the end.
            upper = lower
            for current in range(lower, high + 1):
                if not pivot_key < key_function(items[current]):
                    items[upper], items[current] = items[current], items[upper]
                    upper += 1
            upper -= 1

            left_size = lower - low
            right_size = high - upper

            if left_size < right_size:
                if upper + 1 < high:
                    stack.append((upper + 1, high))
                high = lower - 1
            else:
                if low < lower - 1:
                    stack.append((low, lower - 1))
                low = upper + 1

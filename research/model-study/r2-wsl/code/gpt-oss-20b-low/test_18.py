from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    """From a supplied list of numbers (of length at least two) select and return two that are the closest to each
    other and return them in order (smaller number, larger number)."""
    if len(numbers) < 2:
        raise ValueError("At least two numbers are required")
    sorted_nums = sorted(numbers)
    min_diff = float("inf")
    best_pair = (sorted_nums[0], sorted_nums[1])
    for i in range(len(sorted_nums) - 1):
        a, b = sorted_nums[i], sorted_nums[i + 1]
        diff = b - a
        if diff < min_diff:
            min_diff = diff
            best_pair = (a, b)
    return best_pair



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2]) == (3.9, 4.0)
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0]) == (5.0, 5.9)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.2]) == (2.0, 2.2)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0]) == (2.0, 2.0)
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1]) == (2.2, 3.1)


check(find_closest_elements)

from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    sorted_numbers = sorted(numbers)
    min_diff = float('inf')
    best_pair = (None, None)
    for i in range(len(sorted_numbers) - 1):
        current_diff = sorted_numbers[i+1] - sorted_numbers[i]
        if current_diff < min_diff:
            min_diff = current_diff
            best_pair = (sorted_numbers[i], sorted_numbers[i+1])
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

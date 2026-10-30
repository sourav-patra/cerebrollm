from typing import List

def rescale_to_unit(numbers: List[float]) -> List[float]:
    """Given a list of numbers (at least two elements), apply a linear transform
    so that the smallest number becomes 0 and the largest becomes 1.

    >>> rescale_to_unit([1.0, 2.0, 3.0, 4.0, 5.0])
    [0.0, 0.25, 0.5, 0.75, 1.0]
    """
    if not numbers:
        return []

    min_val = min(numbers)
    max_val = max(numbers)
    span = max_val - min_val

    if span == 0:
        # All numbers are equal; map them all to 0.0
        return [0.0 for _ in numbers]

    return [(x - min_val) / span for x in numbers]



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([2.0, 49.9]) == [0.0, 1.0]
    assert candidate([100.0, 49.9]) == [1.0, 0.0]
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0]) == [0.0, 0.25, 0.5, 0.75, 1.0]
    assert candidate([2.0, 1.0, 5.0, 3.0, 4.0]) == [0.25, 0.0, 1.0, 0.5, 0.75]
    assert candidate([12.0, 11.0, 15.0, 13.0, 14.0]) == [0.25, 0.0, 1.0, 0.5, 0.75]

check(rescale_to_unit)

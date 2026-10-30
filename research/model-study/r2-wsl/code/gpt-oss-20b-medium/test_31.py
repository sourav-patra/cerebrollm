from typing import List
import math

def factorize(n: int) -> List[int]:
    """Return list of prime factors of given integer in ascending order."""
    if n <= 1:
        return []

    factors: List[int] = []

    # factor out 2s
    while n % 2 == 0:
        factors.append(2)
        n //= 2

    # factor out odd numbers
    i = 3
    limit = math.isqrt(n)
    while i <= limit and n > 1:
        while n % i == 0:
            factors.append(i)
            n //= i
            limit = math.isqrt(n)
        i += 2

    if n > 1:
        factors.append(n)

    return factors



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate(2) == [2]
    assert candidate(4) == [2, 2]
    assert candidate(8) == [2, 2, 2]
    assert candidate(3 * 19) == [3, 19]
    assert candidate(3 * 19 * 3 * 19) == [3, 3, 19, 19]
    assert candidate(3 * 19 * 3 * 19 * 3 * 19) == [3, 3, 3, 19, 19, 19]
    assert candidate(3 * 19 * 19 * 19) == [3, 19, 19, 19]
    assert candidate(3 * 2 * 3) == [2, 3, 3]

check(factorize)

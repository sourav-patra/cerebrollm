from typing import List

def factorize(n: int) -> List[int]:
    """Return list of prime factors of given integer in ascending order."""
    if n <= 1:
        return []
    factors: List[int] = []
    # Handle factor 2 separately for efficiency
    while n % 2 == 0:
        factors.append(2)
        n //= 2
    # Check odd factors up to sqrt(n)
    p = 3
    while p * p <= n:
        while n % p == 0:
            factors.append(p)
            n //= p
        p += 2
    # If remaining n is a prime > 2
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

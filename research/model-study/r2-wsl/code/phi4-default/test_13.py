def fibfib(n: int) -> int:
    if n == 0 or n == 1:
        return 0
    elif n == 2:
        return 1
    
    # Initialize base cases
    a, b, c = 0, 0, 1
    
    # Compute the sequence iteratively
    for _ in range(3, n + 1):
        a, b, c = b, c, a + b + c
    
    return c



METADATA = {}


def check(candidate):
    assert candidate(2) == 1
    assert candidate(1) == 0
    assert candidate(5) == 4
    assert candidate(8) == 24
    assert candidate(10) == 81
    assert candidate(12) == 274
    assert candidate(14) == 927


check(fibfib)

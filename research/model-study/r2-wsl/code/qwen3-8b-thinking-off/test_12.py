from typing import Dict

def fib4(n: int) -> int:
    if n == 0 or n == 1 or n == 3:
        return 0
    elif n == 2:
        return 2
    fib_values: Dict[int, int] = {0: 0, 1: 0, 2: 2, 3: 0}
    a, b, c, d = 0, 0, 2, 0
    for _ in range(4, n + 1):
        e = a + b + c + d
        a, b, c, d = b, c, d, e
    return d



METADATA = {}


def check(candidate):
    assert candidate(5) == 4
    assert candidate(8) == 28
    assert candidate(10) == 104
    assert candidate(12) == 386


check(fib4)

import math

def f(n):
    """Return a list of size n where each element at index i (1‑based) is
    factorial(i) if i is even, otherwise the sum of numbers from 1 to i.
    """
    if n <= 0:
        return []
    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:
            result.append(math.factorial(i))
        else:
            result.append(i * (i + 1) // 2)
    return result

def check(candidate):

    assert candidate(5) == [1, 2, 6, 24, 15]
    assert candidate(7) == [1, 2, 6, 24, 15, 720, 28]
    assert candidate(1) == [1]
    assert candidate(3) == [1, 2, 6]

check(f)

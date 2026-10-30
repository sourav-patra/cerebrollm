import math

def f(n):
    return [math.factorial(i) if i % 2 == 0 else i * (i + 1) // 2 for i in range(1, n + 1)]

def check(candidate):

    assert candidate(5) == [1, 2, 6, 24, 15]
    assert candidate(7) == [1, 2, 6, 24, 15, 720, 28]
    assert candidate(1) == [1]
    assert candidate(3) == [1, 2, 6]

check(f)

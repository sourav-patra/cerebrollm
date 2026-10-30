def fib4(n: int) -> int:
    """The Fib4 number sequence is a sequence similar to the Fibonacci sequence that's defined as follows:
    fib4(0) -> 0
    fib4(1) -> 0
    fib4(2) -> 2
    fib4(3) -> 0
    fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4).
    Please write a function to efficiently compute the n-th element of the fib4 number sequence.  Do not use recursion.
    >>> fib4(5)
    4
    >>> fib4(6)
    8
    >>> fib4(7)
    14
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    # Base cases
    base = [0, 0, 2, 0]
    if n < 4:
        return base[n]
    # Use a sliding window of the last four values
    a, b, c, d = base  # a=fib4(n-4), b=fib4(n-3), c=fib4(n-2), d=fib4(n-1)
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

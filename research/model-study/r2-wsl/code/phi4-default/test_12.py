def fib4(n: int) -> int:
    if n == 0 or n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0

    # Initialize the first four values of the sequence
    a, b, c, d = 0, 0, 2, 0

    # Compute the sequence iteratively
    for i in range(4, n + 1):
        # Calculate the next value in the sequence
        next_value = a + b + c + d
        # Update the values for the next iteration
        a, b, c, d = b, c, d, next_value

    return d



METADATA = {}


def check(candidate):
    assert candidate(5) == 4
    assert candidate(8) == 28
    assert candidate(10) == 104
    assert candidate(12) == 386


check(fib4)

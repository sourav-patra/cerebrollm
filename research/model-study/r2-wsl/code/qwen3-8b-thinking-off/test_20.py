import math

def f(n):
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

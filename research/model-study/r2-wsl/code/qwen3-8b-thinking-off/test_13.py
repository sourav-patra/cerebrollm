from typing import Dict

def fibfib(n: int) -> int:
    memo: Dict[int, int] = {}
    def fibfib_helper(n: int) -> int:
        if n in memo:
            return memo[n]
        if n == 0 or n == 1:
            result = 0
        elif n == 2:
            result = 1
        else:
            result = fibfib_helper(n-1) + fibfib_helper(n-2) + fibfib_helper(n-3)
        memo[n] = result
        return result
    return fibfib_helper(n)



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

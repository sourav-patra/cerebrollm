def fibfib(n: int) -> int:
    """
    Efficiently compute the n-th element of the fibfib sequence.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 0
    if n == 2:
        return 1

    # Base matrix for the recurrence
    M = [[1, 1, 1],
         [1, 0, 0],
         [0, 1, 0]]

    def mat_mul(A, B):
        """Multiply two 3x3 matrices."""
        return [
            [
                A[0][0]*B[0][j] + A[0][1]*B[1][j] + A[0][2]*B[2][j]
                for j in range(3)
            ],
            [
                A[1][0]*B[0][j] + A[1][1]*B[1][j] + A[1][2]*B[2][j]
                for j in range(3)
            ],
            [
                A[2][0]*B[0][j] + A[2][1]*B[1][j] + A[2][2]*B[2][j]
                for j in range(3)
            ]
        ]

    def mat_pow(mat, exp):
        """Exponentiate a 3x3 matrix to a non-negative integer power."""
        # Identity matrix
        result = [[1 if i == j else 0 for j in range(3)] for i in range(3)]
        base = mat
        while exp:
            if exp & 1:
                result = mat_mul(result, base)
            base = mat_mul(base, base)
            exp >>= 1
        return result

    # Compute M^(n-2)
    power = mat_pow(M, n - 2)
    # f(n) = power[0][0] * f(2) + power[0][1] * f(1) + power[0][2] * f(0)
    # Since f(2)=1, f(1)=0, f(0)=0, this simplifies to power[0][0]
    return power[0][0]



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

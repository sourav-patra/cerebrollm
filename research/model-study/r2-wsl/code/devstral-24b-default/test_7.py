def is_equal_to_sum_even(n):
    """Evaluate whether the given number n can be written as the sum of exactly 4 positive even numbers
    Example
    is_equal_to_sum_even(4) == False
    is_equal_to_sum_even(6) == False
    is_equal_to_sum_even(8) == True
    """
    # Since we need 4 positive even numbers, the smallest sum is 2 + 2 + 2 + 2 = 8
    if n < 8:
        return False

    # Check if n is even
    if n % 2 != 0:
        return False

    # Try to find 4 positive even numbers that sum to n
    for i in range(2, n, 2):
        for j in range(i, n, 2):
            for k in range(j, n, 2):
                l = n - (i + j + k)
                if l > 0 and l % 2 == 0 and l >= j:
                    return True

    return False

def check(candidate):
    assert candidate(4) == False
    assert candidate(6) == False
    assert candidate(8) == True
    assert candidate(10) == True
    assert candidate(11) == False
    assert candidate(12) == True
    assert candidate(13) == False
    assert candidate(16) == True

check(is_equal_to_sum_even)

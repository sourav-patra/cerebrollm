def is_equal_to_sum_even(n):
    """Evaluate whether the given number n can be written as the sum of exactly 4 positive even numbers
    Example
    is_equal_to_sum_even(4) == False
    is_equal_to_sum_even(6) == False
    is_equal_to_sum_even(8) == True
    """
    # The smallest sum of 4 positive even numbers is 2 + 2 + 2 + 2 = 8
    # All positive even numbers are >= 2
    # So the minimum sum is 8
    # Also, the sum of 4 even numbers is always even
    # So n must be even and >= 8
    
    if n < 8 or n % 2 != 0:
        return False
    
    # For any even n >= 8, we can write it as the sum of 4 positive even numbers
    # For example: 2, 2, 2, n-6 (where n-6 is even and >= 2 when n >= 8)
    return True

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

def is_equal_to_sum_even(n):
    """Evaluate whether the given number n can be written as the sum of exactly 4 positive even numbers
    Example
    is_equal_to_sum_even(4) == False
    is_equal_to_sum_even(6) == False
    is_equal_to_sum_even(8) == True
    """
    # The smallest sum of 4 positive even numbers is 2+2+2+2 = 8
    # Any number less than 8 cannot be expressed as sum of 4 positive even numbers
    if n < 8:
        return False
    
    # The sum of 4 even numbers is always even
    # So if n is odd, it's impossible
    if n % 2 != 0:
        return False
    
    # If n >= 8 and n is even, we can always express it as sum of 4 positive even numbers
    # For example: n = 2 + 2 + 2 + (n-6) where (n-6) is even and positive when n >= 8
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

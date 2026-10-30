def make_a_pile(n):
    """
    Given a positive integer n, you have to make a pile of n levels of stones.
    The first level has n stones.
    The number of stones in the next level is:
        - the next odd number if n is odd.
        - the next even number if n is even.
    Return the number of stones in each level in a list, where element at index
    i represents the number of stones in the level (i+1).

    Examples:
    >>> make_a_pile(3)
    [3, 5, 7]
    """
    if n <= 0:
        return []
    
    result = []
    current = n
    
    for _ in range(n):
        result.append(current)
        # If n is odd, we want next odd numbers (3, 5, 7, 9...)
        # If n is even, we want next even numbers (2, 4, 6, 8...)
        if n % 2 == 1:  # n is odd
            current += 2
        else:  # n is even
            current += 2
    
    return result

def check(candidate):

    # Check some simple cases
    assert candidate(3) == [3, 5, 7], "Test 3"
    assert candidate(4) == [4,6,8,10], "Test 4"
    assert candidate(5) == [5, 7, 9, 11, 13]
    assert candidate(6) == [6, 8, 10, 12, 14, 16]
    assert candidate(8) == [8, 10, 12, 14, 16, 18, 20, 22]

    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"


check(make_a_pile)

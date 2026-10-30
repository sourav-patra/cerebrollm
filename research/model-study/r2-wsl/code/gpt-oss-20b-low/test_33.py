import math

def iscube(a):
    """
    Return True if a is a perfect cube of an integer, otherwise False.
    """
    if a == 0:
        return True
    # Compute the integer cube root (absolute value)
    root = round(abs(a) ** (1/3))
    # Adjust for rounding errors
    while root ** 3 < abs(a):
        root += 1
    while root ** 3 > abs(a):
        root -= 1
    return root ** 3 == abs(a) and (a > 0 or root == 0 or root ** 3 == a)

def check(candidate):

    # Check some simple cases
    assert candidate(1) == True, "First test error: " + str(candidate(1))
    assert candidate(2) == False, "Second test error: " + str(candidate(2))
    assert candidate(-1) == True, "Third test error: " + str(candidate(-1))
    assert candidate(64) == True, "Fourth test error: " + str(candidate(64))
    assert candidate(180) == False, "Fifth test error: " + str(candidate(180))
    assert candidate(1000) == True, "Sixth test error: " + str(candidate(1000))


    # Check some edge cases that are easy to work out by hand.
    assert candidate(0) == True, "1st edge test error: " + str(candidate(0))
    assert candidate(1729) == False, "2nd edge test error: " + str(candidate(1728))


check(iscube)

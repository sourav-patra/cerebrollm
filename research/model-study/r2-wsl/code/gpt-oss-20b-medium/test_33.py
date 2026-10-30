def iscube(a):
    """
    Return True if integer a is a perfect cube, otherwise False.
    """
    if a == 0:
        return True

    x = abs(a)

    # Find an upper bound for the cube root
    high = 1
    while high ** 3 <= x:
        high <<= 1  # multiply by 2

    low = high >> 1  # half of high

    # Binary search for integer cube root
    while low <= high:
        mid = (low + high) // 2
        cube = mid ** 3
        if cube == x:
            return True
        elif cube < x:
            low = mid + 1
        else:
            high = mid - 1

    return False

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

def iscube(a):
    '''
    Write a function that takes an integer a and returns True 
    if this ingeger is a cube of some integer number.
    Note: you may assume the input is always valid.
    Examples:
    iscube(1) ==> True
    iscube(2) ==> False
    iscube(-1) ==> True
    iscube(64) ==> True
    iscube(0) ==> True
    iscube(180) ==> False
    '''
    if a == 0:
        return True
    
    # For negative numbers, check if the absolute value is a perfect cube
    # and the cube root is negative
    if a < 0:
        return iscube(-a) and False  # This won't work directly, let's think again
    
    # Actually, let's just compute the cube root and check
    # For negative numbers, we need to handle them separately
    if a < 0:
        # Check if -a is a perfect cube, and if so, the cube root would be negative
        b = round((-a) ** (1/3))
        # Check b and b+1 and b-1 due to floating point issues
        for candidate in [b - 1, b, b + 1]:
            if candidate ** 3 == -a:
                return True
        return False
    else:
        b = round(a ** (1/3))
        for candidate in [b - 1, b, b + 1]:
            if candidate ** 3 == a:
                return True
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

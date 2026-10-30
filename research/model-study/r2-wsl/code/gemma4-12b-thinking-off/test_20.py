import math

def f(n):
    """ Implement the function f that takes n as a parameter,
    and returns a list of size n, such that the value of the element at index i is the factorial of i if i is even
    or the sum of numbers from 1 to i otherwise.
    i starts from 1.
    the factorial of i is the multiplication of the numbers from 1 to i (1 * 2 * ... * i).
    Example:
    f(5) == [1, 2, 6, 24, 15]
    """
    result = []
    for i in range(1, n + 1):
        if i % 2 == 0:
            # Even index (i is even): factorial of i
            result.append(math.factorial(i))
        else:
            # Odd index (i is odd): sum of numbers from 1 to i
            result.append(sum(range(1, i + 1)))
    
    # The example f(5) == [1, 2, 6, 24, 15] suggests the list is 0-indexed 
    # but the logic applies to the value of i starting from 1.
    # Let's re-verify the example:
    # i=1 (odd): sum(1) = 1
    # i=2 (even): factorial(2) = 2
    # i=3 (odd): sum(1,2,3) = 6
    # i=4 (even): factorial(4) = 24
    # i=5 (odd): sum(1,2,3,4,5) = 15
    # Result: [1, 2, 6, 24, 15]
    
    return result

def check(candidate):

    assert candidate(5) == [1, 2, 6, 24, 15]
    assert candidate(7) == [1, 2, 6, 24, 15, 720, 28]
    assert candidate(1) == [1]
    assert candidate(3) == [1, 2, 6]

check(f)

def specialFilter(nums):
    """Return the count of numbers >10 whose first and last digits are odd."""
    odd_digits = {'1', '3', '5', '7', '9'}
    count = 0
    for n in nums:
        if n > 10:
            s = str(abs(n))
            if s[0] in odd_digits and s[-1] in odd_digits:
                count += 1
    return count

def check(candidate):

    # Check some simple cases
    assert candidate([5, -2, 1, -5]) == 0  
    assert candidate([15, -73, 14, -15]) == 1
    assert candidate([33, -2, -3, 45, 21, 109]) == 2
    assert candidate([43, -12, 93, 125, 121, 109]) == 4
    assert candidate([71, -2, -33, 75, 21, 19]) == 3


    # Check some edge cases that are easy to work out by hand.
    assert candidate([1]) == 0              
    assert candidate([]) == 0                   


check(specialFilter)

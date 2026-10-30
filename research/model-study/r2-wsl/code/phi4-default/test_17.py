def specialFilter(nums):
    def is_first_and_last_digit_odd(n):
        if n < 0:
            n = -n
        digits = str(n)
        if len(digits) == 0:
            return False
        first_digit = int(digits[0])
        last_digit = int(digits[-1])
        return first_digit in {1, 3, 5, 7, 9} and last_digit in {1, 3, 5, 7, 9}

    count = 0
    for num in nums:
        if num > 10 and is_first_and_last_digit_odd(num):
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

def specialFilter(nums):
    def is_odd_digit(digit):
        return digit % 2 == 1
    
    def has_odd_first_and_last_digits(num):
        num = abs(num)
        last_digit = num % 10
        first_digit = num
        while first_digit >= 10:
            first_digit //= 10
        return is_odd_digit(first_digit) and is_odd_digit(last_digit)
    
    count = 0
    for num in nums:
        if num > 10 and has_odd_first_and_last_digits(num):
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

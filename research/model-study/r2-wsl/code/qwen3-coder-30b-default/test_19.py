def count_nums(arr):
    def sum_of_signed_digits(num):
        if num == 0:
            return 0
        
        # Convert to string to easily access digits
        str_num = str(abs(num))
        digits = [int(d) for d in str_num]
        
        # If the number is negative, make the first digit negative
        if num < 0:
            digits[0] = -digits[0]
            
        return sum(digits)
    
    count = 0
    for num in arr:
        if sum_of_signed_digits(num) > 0:
            count += 1
    
    return count

def check(candidate):

    # Check some simple cases
    assert candidate([]) == 0
    assert candidate([-1, -2, 0]) == 0
    assert candidate([1, 1, 2, -2, 3, 4, 5]) == 6
    assert candidate([1, 6, 9, -6, 0, 1, 5]) == 5
    assert candidate([1, 100, 98, -7, 1, -1]) == 4
    assert candidate([12, 23, 34, -45, -56, 0]) == 5
    assert candidate([-0, 1**0]) == 1
    assert candidate([1]) == 1

    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"


check(count_nums)

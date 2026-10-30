def count_nums(arr):
    """
    Write a function count_nums which takes an array of integers and returns
    the number of elements which has a sum of digits > 0.
    If a number is negative, then its first signed digit will be negative:
    e.g. -123 has signed digits -1, 2, and 3.
    >>> count_nums([]) == 0
    >>> count_nums([-1, 11, -11]) == 1
    >>> count_nums([1, 1, 2]) == 3
    """
    def signed_digit_sum(n):
        if n == 0:
            return 0
        if n < 0:
            # For negative numbers, the first digit is negative
            s = str(n)
            # s starts with '-'
            digits = []
            for i, c in enumerate(s):
                if i == 0:
                    # Skip the '-' sign
                    continue
                if i == 1:
                    # First digit after sign is negative
                    digits.append(-int(c))
                else:
                    digits.append(int(c))
            return sum(digits)
        else:
            return sum(int(c) for c in str(n))
    
    count = 0
    for num in arr:
        if signed_digit_sum(num) > 0:
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

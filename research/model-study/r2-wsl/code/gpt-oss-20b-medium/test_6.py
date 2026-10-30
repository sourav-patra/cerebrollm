def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    >>> circular_shift(12, 1)
    "21"
    >>> circular_shift(12, 2)
    "12"
    """
    # Handle negative numbers by preserving the sign
    sign = ''
    if x < 0:
        sign = '-'
        x = -x

    digits = str(x)
    n = len(digits)

    if shift > n:
        return sign + digits[::-1]

    shift_mod = shift % n
    if shift_mod == 0:
        return sign + digits

    return sign + digits[-shift_mod:] + digits[:-shift_mod]

def check(candidate):

    # Check some simple cases
    assert candidate(100, 2) == "001"
    assert candidate(12, 2) == "12"
    assert candidate(97, 8) == "79"
    assert candidate(12, 1) == "21", "This prints if this assert fails 1 (good for debugging!)"

    # Check some edge cases that are easy to work out by hand.
    assert candidate(11, 101) == "11", "This prints if this assert fails 2 (also good for debugging!)"


check(circular_shift)

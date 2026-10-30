def greatest_common_divisor(a: int, b: int) -> int:
    """ Return the greatest common divisor of two integers a and b """
    while b != 0:
        a, b = b, a % b
    return abs(a)

# Example usage:
# print(greatest_common_divisor(3, 5))  # Output: 1
# print(greatest_common_divisor(25, 15))  # Output: 5



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate(3, 7) == 1
    assert candidate(10, 15) == 5
    assert candidate(49, 14) == 7
    assert candidate(144, 60) == 12

check(greatest_common_divisor)

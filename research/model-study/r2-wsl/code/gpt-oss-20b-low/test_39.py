from typing import List

def sort_numbers(numbers: str) -> str:
    """Input is a space-delimited string of numberals from 'zero' to 'nine'.
    Valid choices are 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight' and 'nine'.
    Return the string with numbers sorted from smallest to largest.
    >>> sort_numbers('three one five')
    'one three five'
    """
    word_to_digit = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
    }
    digit_to_word = {v: k for k, v in word_to_digit.items()}

    if not numbers.strip():
        return ''

    words = numbers.split()
    # Filter out any invalid words (optional)
    filtered = [w for w in words if w in word_to_digit]
    sorted_digits = sorted(word_to_digit[w] for w in filtered)
    sorted_words = [digit_to_word[d] for d in sorted_digits]
    return ' '.join(sorted_words)



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('') == ''
    assert candidate('three') == 'three'
    assert candidate('three five nine') == 'three five nine'
    assert candidate('five zero four seven nine eight') == 'zero four five seven eight nine'
    assert candidate('six five four three two one zero') == 'zero one two three four five six'

check(sort_numbers)

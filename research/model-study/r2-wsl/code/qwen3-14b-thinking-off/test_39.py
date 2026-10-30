from typing import List

def sort_numbers(numbers: str) -> str:
    num_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    num_dict = {word: idx for idx, word in enumerate(num_words)}
    sorted_numbers = sorted(numbers.split(), key=lambda x: num_dict[x])
    return ' '.join(sorted_numbers)



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

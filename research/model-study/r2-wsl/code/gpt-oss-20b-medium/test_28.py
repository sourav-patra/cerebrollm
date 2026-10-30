import re

def anti_shuffle(s: str) -> str:
    """
    Return a string where each word (sequence of non-space characters) is sorted
    by ascending ASCII value, while preserving the original spaces.
    """
    if not s:
        return s
    tokens = re.findall(r'\S+|\s+', s)
    sorted_tokens = [
        ''.join(sorted(tok)) if not tok.isspace() else tok
        for tok in tokens
    ]
    return ''.join(sorted_tokens)

def check(candidate):

    # Check some simple cases
    assert candidate('Hi') == 'Hi'
    assert candidate('hello') == 'ehllo'
    assert candidate('number') == 'bemnru'
    assert candidate('abcd') == 'abcd'
    assert candidate('Hello World!!!') == 'Hello !!!Wdlor'
    assert candidate('') == ''
    assert candidate('Hi. My name is Mister Robot. How are you?') == '.Hi My aemn is Meirst .Rboot How aer ?ouy'
    # Check some edge cases that are easy to work out by hand.
    assert True


check(anti_shuffle)

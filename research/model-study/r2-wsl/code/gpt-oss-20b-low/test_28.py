def anti_shuffle(s: str) -> str:
    """
    Return a string where each word (separated by spaces) has its characters
    sorted in ascending ASCII order, preserving the original word order and
    spaces.
    """
    # Split on spaces, preserving empty strings for consecutive spaces
    parts = s.split(' ')
    # Sort characters in each part
    sorted_parts = [''.join(sorted(part)) for part in parts]
    # Rejoin with single spaces
    return ' '.join(sorted_parts)

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

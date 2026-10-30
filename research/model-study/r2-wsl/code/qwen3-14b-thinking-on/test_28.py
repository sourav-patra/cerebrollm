import re

def anti_shuffle(s):
    tokens = re.findall(r'\S+|\s+', s)
    result = []
    for token in tokens:
        if token.isspace():
            result.append(token)
        else:
            sorted_token = ''.join(sorted(token))
            result.append(sorted_token)
    return ''.join(result)

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

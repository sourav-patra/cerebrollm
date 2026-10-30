def anti_shuffle(s):
    import re
    words = re.split(r'(\s+)', s)
    ordered_words = []
    for word in words:
        if word.strip():
            ordered = ''.join(sorted(word))
            ordered_words.append(ordered)
        else:
            ordered_words.append(word)
    return ''.join(ordered_words)

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

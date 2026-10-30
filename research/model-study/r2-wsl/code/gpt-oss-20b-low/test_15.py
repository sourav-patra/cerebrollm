import re

def split_words(txt):
    """
    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you
    should split on commas ',' if no commas exists you should return the number of lower-case letters with odd order in the
    alphabet, ord('a') = 0, ord('b') = 1, ... ord('z') = 25
    """
    # If there is any whitespace, split on it
    if re.search(r'\s', txt):
        return txt.split()
    # If there is a comma, split on it
    if ',' in txt:
        return txt.split(',')
    # Otherwise count lower-case letters with odd alphabet index
    count = sum(1 for ch in txt if 'a' <= ch <= 'z' and ((ord(ch) - ord('a')) % 2 == 1))
    return count

def check(candidate):

    assert candidate("Hello world!") == ["Hello","world!"]
    assert candidate("Hello,world!") == ["Hello","world!"]
    assert candidate("Hello world,!") == ["Hello","world,!"]
    assert candidate("Hello,Hello,world !") == ["Hello,Hello,world","!"]
    assert candidate("abcdef") == 3
    assert candidate("aaabb") == 2
    assert candidate("aaaBb") == 1
    assert candidate("") == 0

check(split_words)

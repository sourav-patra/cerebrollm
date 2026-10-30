def split_words(txt):
    """
    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you
    should split on commas ',' if no commas exists you should return the number of lower-case letters with odd order in the
    alphabet, ord('a') = 0, ord('b') = 1, ... ord('z') = 25
    """
    # Check for whitespace
    if any(c.isspace() for c in txt):
        return txt.split()
    # Check for commas
    if ',' in txt:
        return txt.split(',')
    # Count lower-case letters with odd alphabet index
    count = 0
    for ch in txt:
        if 'a' <= ch <= 'z':
            if (ord(ch) - ord('a')) % 2 == 1:
                count += 1
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

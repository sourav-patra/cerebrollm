def split_words(txt):
    '''
    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you
    should split on commas ',' if no commas exists you should return the number of lower-case letters with odd order in the
    alphabet, ord('a') = 0, ord('b') = 1, ... ord('z') = 25
    Examples
    split_words("Hello world!") ➞ ["Hello", "world!"]
    split_words("Hello,world!") ➞ ["Hello", "world!"]
    split_words("abcdef") == 3 
    '''
    # Check if there are whitespaces
    if ' ' in txt:
        return txt.split()
    # Check if there are commas
    elif ',' in txt:
        return txt.split(',')
    else:
        # Count lowercase letters with odd order in the alphabet
        # ord('a') = 0 (even), ord('b') = 1 (odd), ord('c') = 2 (even), etc.
        # So odd order means: b, d, f, h, j, l, n, p, r, t, v, x, z
        count = 0
        for char in txt:
            if char.islower():
                # ord('a') = 97, so ord(char) - ord('a') gives 0 for 'a', 1 for 'b', etc.
                order = ord(char) - ord('a')
                if order % 2 == 1:
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

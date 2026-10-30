def split_words(txt):
    import re
    if re.search(r'\s', txt):
        return txt.split()
    elif re.search(r',', txt):
        return txt.split(',')
    else:
        count = 0
        for char in txt:
            if 'a' <= char <= 'z':
                if (ord(char) - ord('a')) % 2 == 1:
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

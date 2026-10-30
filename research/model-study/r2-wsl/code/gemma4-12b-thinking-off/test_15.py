def split_words(txt):
    # Check for whitespace
    if any(char.isspace() for char in txt):
        return txt.split()
    
    # Check for commas
    if ',' in txt:
        return [word for word in txt.split(',') if word]
    
    # No whitespace and no commas: count lowercase letters with odd alphabet order
    # ord('a') = 0 (even), ord('b') = 1 (odd), ..., ord('z') = 25 (odd)
    count = 0
    for char in txt:
        if 'a' <= char <= 'z':
            # Calculate position: ord(char) - ord('a')
            # If position is odd, increment count
            if (ord(char) - ord('a')) % 2 != 0:
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

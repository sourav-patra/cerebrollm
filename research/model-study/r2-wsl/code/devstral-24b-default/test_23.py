def encrypt(s):
    """Create a function encrypt that takes a string as an argument and
    returns a string encrypted with the alphabet being rotated.
    The alphabet should be rotated in a manner such that the letters
    shift down by two multiplied to two places.
    For example:
    encrypt('hi') returns 'lm'
    encrypt('asdfghjkl') returns 'ewhjklnop'
    encrypt('gf') returns 'kj'
    encrypt('et') returns 'ix'
    """
    result = []
    shift = 2 * 2  # Shift by 4 places

    for char in s:
        if char.isalpha():
            start = ord('a') if char.islower() else ord('A')
            # Calculate new character position with wrap-around using modulo
            new_char = chr(start + (ord(char) - start + shift) % 26)
            result.append(new_char)
        else:
            # Non-alphabetic characters remain unchanged
            result.append(char)

    return ''.join(result)

# Test cases
print(encrypt('hi'))  # returns 'lm'
print(encrypt('asdfghjkl'))  # returns 'ewhjklnop'
print(encrypt('gf'))  # returns 'kj'
print(encrypt('et'))  # returns 'ix'

def check(candidate):

    # Check some simple cases
    assert candidate('hi') == 'lm', "This prints if this assert fails 1 (good for debugging!)"
    assert candidate('asdfghjkl') == 'ewhjklnop', "This prints if this assert fails 1 (good for debugging!)"
    assert candidate('gf') == 'kj', "This prints if this assert fails 1 (good for debugging!)"
    assert candidate('et') == 'ix', "This prints if this assert fails 1 (good for debugging!)"

    assert candidate('faewfawefaewg')=='jeiajeaijeiak', "This prints if this assert fails 1 (good for debugging!)"
    assert candidate('hellomyfriend')=='lippsqcjvmirh', "This prints if this assert fails 2 (good for debugging!)"
    assert candidate('dxzdlmnilfuhmilufhlihufnmlimnufhlimnufhfucufh')=='hbdhpqrmpjylqmpyjlpmlyjrqpmqryjlpmqryjljygyjl', "This prints if this assert fails 3 (good for debugging!)"

    # Check some edge cases that are easy to work out by hand.
    assert candidate('a')=='e', "This prints if this assert fails 2 (also good for debugging!)"


check(encrypt)

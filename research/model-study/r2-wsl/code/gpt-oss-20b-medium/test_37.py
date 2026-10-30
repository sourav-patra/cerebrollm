def check_if_last_char_is_a_letter(txt):
    """
    Return True if the last character of txt is an alphabetical character
    and is not part of a word (i.e., the preceding character is a space
    or there is no preceding character). Otherwise, return False.
    """
    if not txt:
        return False
    last_char = txt[-1]
    if not last_char.isalpha():
        return False
    if len(txt) == 1:
        return True
    return txt[-2] == ' '

def check(candidate):

    # Check some simple cases
    assert candidate("apple") == False
    assert candidate("apple pi e") == True
    assert candidate("eeeee") == False
    assert candidate("A") == True
    assert candidate("Pumpkin pie ") == False
    assert candidate("Pumpkin pie 1") == False
    assert candidate("") == False
    assert candidate("eeeee e ") == False
    assert candidate("apple pie") == False
    assert candidate("apple pi e ") == False

    # Check some edge cases that are easy to work out by hand.
    assert True


check(check_if_last_char_is_a_letter)

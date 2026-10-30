def check_if_last_char_is_a_letter(txt):
    import re
    if not txt:
        return False
    words = re.split(r'\s+', txt)
    if not words:
        return False
    last_word = words[-1]
    if not last_word:
        return False
    if not last_word[-1].isalpha():
        return False
    return True

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

def check_if_last_char_is_a_letter(txt):
    if not txt:
        return False
    
    # Remove trailing whitespace
    txt = txt.rstrip()
    
    if not txt:
        return False
    
    # Get the last character
    last_char = txt[-1]
    
    # Check if it's an alphabetical character
    if not last_char.isalpha():
        return False
    
    # Check if it's not part of a word (i.e., preceded by a space or is the only character)
    if len(txt) == 1:
        return True
    
    # If the character before the last one is a space, then the last character is standalone
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

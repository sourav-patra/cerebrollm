def reverse_delete(s, c):
    # Create a set of characters to delete for faster lookup
    delete_set = set(c)
    
    # Filter out characters from s that are in delete_set
    result = ''.join(char for char in s if char not in delete_set)
    
    # Check if the resulting string is a palindrome
    is_palindrome = result == result[::-1]
    
    # Return the result string and the palindrome check
    return (result, is_palindrome)

def check(candidate):

    assert candidate("abcde","ae") == ('bcd',False)
    assert candidate("abcdef", "b") == ('acdef',False)
    assert candidate("abcdedcba","ab") == ('cdedc',True)
    assert candidate("dwik","w") == ('dik',False)
    assert candidate("a","a") == ('',True)
    assert candidate("abcdedcba","") == ('abcdedcba',True)
    assert candidate("abcdedcba","v") == ('abcdedcba',True)
    assert candidate("vabba","v") == ('abba',True)
    assert candidate("mamma", "mia") == ("", True)

check(reverse_delete)

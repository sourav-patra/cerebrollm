def cycpattern_check(a, b):
    """
    Return True if any rotation of string b is a substring of string a.
    """
    if not b:
        return True  # empty string is always a substring
    n = len(b)
    for i in range(n):
        rot = b[i:] + b[:i]
        if rot in a:
            return True
    return False

def check(candidate):

    # Check some simple cases
    #assert True, "This prints if this assert fails 1 (good for debugging!)"

    # Check some edge cases that are easy to work out by hand.
    #assert True, "This prints if this assert fails 2 (also good for debugging!)"
    assert  candidate("xyzw","xyw") == False , "test #0"
    assert  candidate("yello","ell") == True , "test #1"
    assert  candidate("whattup","ptut") == False , "test #2"
    assert  candidate("efef","fee") == True , "test #3"
    assert  candidate("abab","aabb") == False , "test #4"
    assert  candidate("winemtt","tinem") == True , "test #5"


check(cycpattern_check)

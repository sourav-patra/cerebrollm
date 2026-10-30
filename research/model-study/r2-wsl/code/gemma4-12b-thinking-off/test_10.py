def check_dict_case(dict_input):
    """
    Given a dictionary, return True if all keys are strings in lower 
    case or all keys are strings in upper case, else return False.
    The function should return False if the given dictionary is empty.
    """
    if not dict_input:
        return False
    
    keys = list(dict_input.keys())
    
    # Check if all keys are strings
    if not all(isinstance(k, str) for k in keys):
        return False
    
    all_lower = True
    all_upper = True
    
    for k in keys:
        if not (k == k.lower()):
            all_lower = False
        if not (k == k.upper()):
            all_upper = False
            
    return all_lower or all_upper

def check(candidate):

    # Check some simple cases
    assert candidate({"p":"pineapple", "b":"banana"}) == True, "First test error: " + str(candidate({"p":"pineapple", "b":"banana"}))
    assert candidate({"p":"pineapple", "A":"banana", "B":"banana"}) == False, "Second test error: " + str(candidate({"p":"pineapple", "A":"banana", "B":"banana"}))
    assert candidate({"p":"pineapple", 5:"banana", "a":"apple"}) == False, "Third test error: " + str(candidate({"p":"pineapple", 5:"banana", "a":"apple"}))
    assert candidate({"Name":"John", "Age":"36", "City":"Houston"}) == False, "Fourth test error: " + str(candidate({"Name":"John", "Age":"36", "City":"Houston"}))
    assert candidate({"STATE":"NC", "ZIP":"12345" }) == True, "Fifth test error: " + str(candidate({"STATE":"NC", "ZIP":"12345" }))      
    assert candidate({"fruit":"Orange", "taste":"Sweet" }) == True, "Fourth test error: " + str(candidate({"fruit":"Orange", "taste":"Sweet" }))      


    # Check some edge cases that are easy to work out by hand.
    assert candidate({}) == False, "1st edge test error: " + str(candidate({}))


check(check_dict_case)

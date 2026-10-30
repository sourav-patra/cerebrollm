def next_smallest(lst):
    if len(lst) < 2:
        return None
    min_val = min(lst)
    new_lst = [x for x in lst if x != min_val]
    if not new_lst:
        return None
    return min(new_lst)

def check(candidate):

    # Check some simple cases
    assert candidate([1, 2, 3, 4, 5]) == 2
    assert candidate([5, 1, 4, 3, 2]) == 2
    assert candidate([]) == None
    assert candidate([1, 1]) == None
    assert candidate([1,1,1,1,0]) == 1
    assert candidate([1, 0**0]) == None
    assert candidate([-35, 34, 12, -45]) == -35

    # Check some edge cases that are easy to work out by hand.
    assert True


check(next_smallest)

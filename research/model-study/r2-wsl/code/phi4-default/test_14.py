def correct_bracketing(brackets: str) -> bool:
    """ 
    brackets is a string of "(" and ")".
    Return True if every opening bracket has a corresponding closing bracket.
    """
    balance = 0
    for char in brackets:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
        if balance < 0:
            return False
    return balance == 0

# Example usage:
# print(correct_bracketing("("))      # False
# print(correct_bracketing("()"))     # True
# print(correct_bracketing("(()())")) # True
# print(correct_bracketing(")(()"))   # False



METADATA = {}


def check(candidate):
    assert candidate("()")
    assert candidate("(()())")
    assert candidate("()()(()())()")
    assert candidate("()()((()()())())(()()(()))")
    assert not candidate("((()())))")
    assert not candidate(")(()")
    assert not candidate("(")
    assert not candidate("((((")
    assert not candidate(")")
    assert not candidate("(()")
    assert not candidate("()()(()())())(()")
    assert not candidate("()()(()())()))()")


check(correct_bracketing)

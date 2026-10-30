def correct_bracketing(brackets: str) -> bool:
    """
    brackets is a string of "(" and ")".
    return True if every opening bracket has a corresponding closing bracket.
    """
    count = 0
    for ch in brackets:
        if ch == '(':
            count += 1
        elif ch == ')':
            count -= 1
            if count < 0:
                return False
        else:
            # ignore any other characters
            continue
    return count == 0



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

def vowels_count(s: str) -> int:
    """Return the number of vowels in the string `s`.
    Vowels are 'a', 'e', 'i', 'o', 'u' (case‑insensitive).
    The letter 'y' is counted as a vowel only if it appears at the end of the string.
    """
    if not s:
        return 0

    s_lower = s.lower()
    vowels = set("aeiou")
    count = 0

    for i, ch in enumerate(s_lower):
        if ch in vowels:
            count += 1
        elif ch == 'y' and i == len(s_lower) - 1:
            count += 1

    return count

def check(candidate):

    # Check some simple cases
    assert candidate("abcde") == 2, "Test 1"
    assert candidate("Alone") == 3, "Test 2"
    assert candidate("key") == 2, "Test 3"
    assert candidate("bye") == 1, "Test 4"
    assert candidate("keY") == 2, "Test 5"
    assert candidate("bYe") == 1, "Test 6"
    assert candidate("ACEDY") == 3, "Test 7"

    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"


check(vowels_count)

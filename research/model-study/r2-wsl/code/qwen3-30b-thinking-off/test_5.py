Okay, let's see. I need to implement a function that counts the distinct characters in a string, ignoring case. So, for example, 'x' and 'X' should be considered the same character.

Hmm, the problem says "regardless of case," so I should convert the entire string to either lower or upper case first. Then, I can count the unique characters.

Wait, the example given is 'xyzXYZ' which should return 3. Let's check: converting to lower, it's 'xyzxyz', so the unique characters are x, y, z. So three distinct. That makes sense.

Another example: 'Jerry' becomes 'jerry', so unique letters are j, e, r, y. Wait, 'Jerry' has J, e, r, r, y. So distinct are J, e, r, y. But when case is ignored, J and j are same. So converting to lower, it's 'jerry', so unique letters are j, e, r, y. So 4, which matches the example.

So the plan is: convert the string to all lowercase (or uppercase), then create a set of the characters, and return the size of the set.

Wait, sets in Python automatically remove duplicates, so converting the string to a set will give unique elements. So the steps are:

1. Convert the input string to lowercase (or uppercase) to ignore case.
2. Convert the string to a set.
3. Return the length of the set.

Let me test with the examples.

For 'xyzXYZ', converting to lower gives 'xyzxyz', set is {'x', 'y', 'z'}, size 3. Correct.

For 'Jerry', lower is 'jerry', set is {'j', 'e', 'r', 'y'}, size 4. Correct.

So the code should be straightforward.

Now, the function needs to be implemented. Let's write it.

def count_distinct_characters(string: str) -> int:
    return len(set(string.lower()))

Wait, that's it? Let me check.

Yes, because string.lower() converts all to lower, then set() removes duplicates, len() gives the count.

Wait, but what about non-alphabet characters? The problem says "distinct characters", so even if they are numbers or symbols, they count as distinct. But the examples given are all letters, but the function should handle any characters.

For example, if the string is 'aA1!', then lower would be 'aa1!', set is {'a', '1', '!'}, so count is 3. Which is correct.

So the code should work for any string.

So the function is simply converting to lower, making a set, and returning the length.

So the code would be:

def count_distinct_characters(string: str) -> int:
    return len(set(string.lower()))

Wait, but the problem says "distinct characters (regardless of case)", so this approach is correct.

Let me check the examples again.

First example: 'xyzXYZ' → lower is 'xyzxyz' → set has 3 elements. Correct.

Second example: 'Jerry' → 'jerry' → set has 4 elements. Correct.

Yes, this should work.

So the code is very simple. I don't need any imports because string.lower() is a built-in method.

So the complete function is as above.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So I need to write the function, and if there are any imports needed, include them. But in this case, no imports are needed because string methods are built-in.

So the code block should be:

def count_distinct_characters(string: str) -> int:
    return len(set(string.lower()))

Yes, that's it. Let me make sure there's no edge cases I'm missing.

What about empty string? If string is empty, len(set(''.lower())) is len(set('')) which is 0. So returns 0. Which is correct.

Another test case: 'aAaA' → lower is 'aaaa', set has 1 element. So returns 1. Correct.

So the code should handle all cases.

Therefore, the correct implementation is as above.
</think>

def count_distinct_characters(string: str) -> int:
    return len(set(string.lower()))



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('') == 0
    assert candidate('abcde') == 5
    assert candidate('abcde' + 'cade' + 'CADE') == 5
    assert candidate('aaaaAAAAaaaa') == 1
    assert candidate('Jerry jERRY JeRRRY') == 5

check(count_distinct_characters)

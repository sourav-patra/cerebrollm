Okay, let's see. I need to implement a function that counts how many times a substring appears in a string, including overlapping occurrences. The examples given are important. For example, 'aaa' with substring 'a' should return 3, which makes sense because each 'a' is a separate occurrence. Then 'aaaa' with 'aa' should return 3. Let me think why.

Wait, for 'aaaa' and 'aa', the substrings would be positions 0-1, 1-2, 2-3. So three times. So overlapping is allowed. So the standard string count method in Python doesn't count overlapping, right? Like, if I do 'aaaa'.count('aa'), it would return 2, but the problem says it should return 3. So I can't use the built-in count method directly.

So I need to find a way to check each possible starting position. For each index in the string, check if the substring starts there. So for the string of length n, and substring of length m, the possible starting indices are from 0 to n - m.

Wait, for example, in 'aaaa' (length 4), substring 'aa' (length 2). The starting indices are 0, 1, 2. So 3 positions. So the count would be 3.

So the approach is to loop through each possible starting index, check if the substring matches starting at that index, and count how many times that happens.

So the function should iterate from i=0 to len(string) - len(substring), and for each i, check if string[i:i+len(substring)] equals substring. If yes, increment the count.

Wait, but what if the substring is empty? The problem says the examples include empty string. For example, the first example is how_many_times('', 'a') returns 0. So if the substring is empty, but in the problem statement, the substring is given as 'a' in that case. Wait, the first example is string is empty, substring is 'a', so returns 0. So the code should handle cases where the substring is longer than the string, which would return 0.

So the code should check for the length of the substring. If the substring is longer than the string, return 0. Otherwise, loop through each possible start.

So the steps are:

1. If the substring is empty, return 0? Wait, but the problem's examples don't have that. Wait, the problem says "substring: str", so it's possible that substring is empty. But according to the problem's examples, the first test case is string empty, substring 'a', which returns 0. So maybe the code should handle substring being empty. Wait, but if substring is empty, how many times does it occur? Well, in Python, an empty string is considered to occur at every position, but the problem's examples don't cover that. However, the problem's test cases probably don't include empty substring. But to be safe, perhaps the code should handle it.

Wait, but the problem's examples don't have substring as empty. Let's see the problem statement. The function's parameters are string and substring, both strings. So the code should handle all possible cases.

But according to the problem's examples, the first test case is string empty, substring 'a', which returns 0. So for the code, if the substring is empty, perhaps the count is 0, or maybe it's infinite. But in practice, in Python, the count of empty string in a string is len(string) + 1. But the problem's examples don't mention that, so perhaps the problem assumes that substring is non-empty. However, the problem statement says "substring: str", so it's possible that it's empty. But the problem's examples don't include that case, so maybe the code should handle it as per the problem's requirements.

Wait, but the problem says "Count overlaping cases." So for example, if substring is empty, but the problem's test cases probably don't include that. Let's proceed under the assumption that the substring is non-empty, but the code should handle the case where substring is empty by returning 0, or perhaps the problem's test cases don't have that.

But looking at the problem's examples, the first test case is string empty, substring 'a', which returns 0. So the code should handle when the string is shorter than the substring. For example, if the string is 'a' and substring is 'aa', then the count is 0.

So the code should check if len(substring) is 0. If so, return 0 (since the problem's examples don't handle empty substring, and the problem's test cases probably don't include it, but to be safe, perhaps return 0 for empty substring). Wait, but in Python, if substring is empty, then the count would be len(string) + 1, but the problem's examples don't cover that. However, the problem's test cases probably don't include empty substring, so perhaps the code can assume that substring is non-empty. But to be safe, let's check.

Wait, the problem's first example is how_many_times('', 'a'), which is string empty, substring 'a', returns 0. So the code should handle when the string is shorter than the substring. So the code should check if len(substring) > len(string), then return 0.

So the plan is:

- If the substring is empty, return 0 (since the problem's examples don't have this case, but to prevent errors, perhaps handle it).

- Else, loop through each possible starting index i from 0 to len(string) - len(substring), and check if string[i:i+len(substring)] == substring.

- Count the number of matches.

So for example, 'aaa' and 'a' would loop i from 0 to 3-1=2 (since len(string)=3, len(substring)=1, so 3-1=2). So i=0,1,2. Each time, string[i:i+1] is 'a', so count 3.

Another example: 'aaaa' (len 4), substring 'aa' (len 2). So i ranges from 0 to 4-2=2. So i=0,1,2. Each time, check if the substring matches. So 3 times.

So the code would be:

def how_many_times(string: str, substring: str) -> int:
    if not substring:
        return 0
    count = 0
    n = len(string)
    m = len(substring)
    for i in range(n - m + 1):
        if string[i:i+m] == substring:
            count += 1
    return count

Wait, but in Python, the range for i would be from 0 to n - m inclusive. Because range(n - m + 1) gives 0 to n - m.

Yes. For example, if n=4, m=2, then n - m +1 = 3, so range(3) is 0,1,2. Which is correct.

Testing the examples:

First example: string is '', substring 'a'. n=0, m=1. n - m +1 = 0 -1 +1 = 0. So the loop runs 0 times, returns 0. Correct.

Second example: 'aaa', 'a'. n=3, m=1. n - m +1 = 3. So i from 0 to 2. Each time, string[i:i+1] is 'a', so count 3. Correct.

Third example: 'aaaa', 'aa'. n=4, m=2. n - m +1 = 3. So i=0,1,2. Each time, check if 'aa' matches. So 3 times. Correct.

Another test case: 'abababa', 'aba' should return 3 (positions 0, 2, 4).

So the code should handle that.

Now, check if the substring is empty. If substring is empty, the code returns 0. Which is correct, because the problem's examples don't have that case, but it's a safe default.

So the code should be as written.

Now, check if there are any edge cases. For example, if the substring is longer than the string, like string 'a', substring 'aa', then n=1, m=2. n - m +1 = 1-2+1=0, so loop runs 0 times, returns 0. Correct.

Another edge case: string 'a', substring 'a' → returns 1.

Yes.

So the code should work.

Now, the problem says to return the complete executable function with any needed imports. But in this case, no imports are needed. So the code is as written.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should be:

def how_many_times(string: str, substring: str) -> int:
    if not substring:
        return 0
    count = 0
    n = len(string)
    m = len(substring)
    for i in range(n - m + 1):
        if string[i:i+m] == substring:
            count += 1
    return count

Wait, but in Python, the 'if not substring' checks if substring is empty. Because empty string is falsy. So that's correct.

Testing the first example: string is empty, substring 'a' → substring is not empty, so proceed. n=0, m=1. n - m +1 = 0 -1 +1 = 0. So range(0) is empty, returns 0. Correct.

Another test case: string 'a', substring 'a' → returns 1.

Yes.

So this code should handle all the cases.

I think that's it. So the code is correct.
</think>

def how_many_times(string: str, substring: str) -> int:
    if not substring:
        return 0
    count = 0
    n = len(string)
    m = len(substring)
    for i in range(n - m + 1):
        if string[i:i+m] == substring:
            count += 1
    return count



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('', 'x') == 0
    assert candidate('xyxyxyx', 'x') == 4
    assert candidate('cacacacac', 'cac') == 4
    assert candidate('john doe', 'john') == 1

check(how_many_times)

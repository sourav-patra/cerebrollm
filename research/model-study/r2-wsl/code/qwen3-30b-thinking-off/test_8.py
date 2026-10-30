Okay, let's see. I need to implement a function called add that takes a list of integers. The task is to add the even elements that are at odd indices. Wait, odd indices. So indices start at 0, right? So odd indices would be 1, 3, 5, etc.

Wait, the example given is add([4, 2, 6, 7]) returns 2. Let's check that. The list is [4, 2, 6, 7]. Let's index them: index 0 is 4, index 1 is 2, index 2 is 6, index 3 is 7.

We need elements at odd indices (1, 3, ...). So index 1 is 2, index 3 is 7. Now, check if those elements are even. 2 is even, 7 is odd. So only 2 contributes. So sum is 2. That matches the example.

So the steps are: iterate over the list, check for indices that are odd (i % 2 == 1), then check if the element at that index is even (element % 2 == 0), and sum those elements.

Wait, but the problem says "add the even elements that are at odd indices." So for each element at an odd index, if it's even, add it to the sum.

So in code, for each index i in the list, if i is odd (i % 2 == 1) and lst[i] is even (lst[i] % 2 == 0), then add lst[i] to the sum.

Wait, but the example: index 1 is 2, which is even. So sum is 2. Correct.

Another example: let's say the list is [1, 3, 5, 7]. All elements at odd indices (1 and 3) are 3 and 7, which are odd. So sum is 0.

Another example: [10, 20, 30, 40]. Indices 1 and 3: 20 and 40. Both even. Sum is 60.

So the code should loop through the list, check for odd indices, check if element is even, sum them.

Now, how to code this. Let's think.

We can loop through the list with index. For i in range(len(lst)):

if i is odd (i % 2 == 1), then check if lst[i] is even (lst[i] % 2 == 0), then add to sum.

Wait, but the problem says "non-empty list", so we don't have to handle empty lists.

So the function would be:

def add(lst):
    total = 0
    for i in range(len(lst)):
        if i % 2 == 1 and lst[i] % 2 == 0:
            total += lst[i]
    return total

Wait, let's test with the example. lst = [4,2,6,7]. i=0: even index, skip. i=1: odd index. lst[1] is 2, which is even. Add to total. i=2: even index. i=3: odd index. lst[3] is 7, which is odd. So total is 2. Correct.

Another test case: [1, 2, 3, 4]. Indices 1 and 3. Elements 2 and 4. Both even. Sum is 6.

So the code should work.

Wait, but the problem says "add the even elements that are at odd indices." So the code is correct.

Now, check if there are any edge cases. For example, a list with one element. Since the list is non-empty, but if it's length 1, then the only index is 0 (even), so no elements to add. So returns 0.

Another case: [5, 6, 7, 8]. Indices 1 and 3. Elements 6 and 8. Both even. Sum 14.

So the code should handle that.

Now, the code as written should work.

Wait, but in Python, the modulo for negative numbers might be tricky, but the problem states integers, but the example uses positive. The problem says "non-empty list of integers", but the example uses positive. However, the code should handle evenness correctly. For example, -2 is even. So if the list has a negative even number at an odd index, it should be added.

But the problem statement doesn't specify, but the code should handle it as per standard even check.

So the code as written uses lst[i] % 2 == 0, which correctly checks for evenness, including negative numbers.

So the code should be correct.

Now, the problem says to return the complete executable function with any needed imports. But in this case, no imports are needed. So the code is just the function.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should be:

def add(lst):
    total = 0
    for i in range(len(lst)):
        if i % 2 == 1 and lst[i] % 2 == 0:
            total += lst[i]
    return total

Wait, but let's check if the example in the problem matches. The example says add([4, 2, 6, 7]) returns 2. Which is correct.

Another possible way: using list comprehensions. But the problem says to implement the function, so the loop is fine.

So the code should be as above.

Wait, but let's check if the index starts at 0. Yes, in Python, lists are 0-based. So index 1 is the second element, which is odd index.

Yes.

So the code is correct.

I think that's it. So the function is as written.
</think>

def add(lst):
    total = 0
    for i in range(len(lst)):
        if i % 2 == 1 and lst[i] % 2 == 0:
            total += lst[i]
    return total

def check(candidate):

    # Check some simple cases
    assert candidate([4, 88]) == 88
    assert candidate([4, 5, 6, 7, 2, 122]) == 122
    assert candidate([4, 0, 6, 7]) == 0
    assert candidate([4, 4, 6, 8]) == 12

    # Check some edge cases that are easy to work out by hand.
    

check(add)

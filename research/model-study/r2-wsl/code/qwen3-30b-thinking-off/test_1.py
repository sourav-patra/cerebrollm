Okay, let's see. I need to implement this strange_sort_list function. The problem says to sort the list in a way where you start with the minimum, then the maximum of the remaining, then the minimum again, and so on.

Hmm, so for example, [1,2,3,4] becomes [1,4,2,3]. Let me think about how to approach this.

First, maybe sort the list. Then, take the smallest, then the largest from what's left, then the next smallest, etc. So the idea is to alternate between taking the smallest and largest elements from the remaining list.

Wait, but how to do that efficiently. Let's think step by step.

Let's take the example [1,2,3,4]. Sort it to [1,2,3,4]. Then, take the first element (1), then the last (4), then the next first (2), then the next last (3). So the result is [1,4,2,3].

Another example: [5,5,5,5]. Sorting gives [5,5,5,5]. Taking min and max each time, but since all are same, it's just [5,5,5,5].

So the plan is:

1. Sort the input list.
2. Then, create a new list by alternately taking the smallest remaining and largest remaining elements.

Wait, but how to do that. Let's think of using two pointers. One at the start (for min) and one at the end (for max). Then, take the start, then the end, then start+1, then end-1, etc.

Yes, that's a common approach for such problems. So for a sorted list, we can have two pointers, left and right. We'll take elements from left, then right, then left+1, then right-1, etc., until all elements are taken.

So for the sorted list, the steps would be:

- Initialize left = 0, right = len(lst) -1.
- While left <= right:
   - If left <= right, append lst[left], then left +=1
   - If left <= right, append lst[right], then right -=1

Wait, but in the example [1,2,3,4], sorted is [1,2,3,4]. Let's see:

left starts at 0, right at 3.

First append lst[0] =1, left becomes 1.

Then append lst[3] =4, right becomes 2.

Now left=1, right=2.

Append lst[1] =2, left becomes 2.

Append lst[2] =3, right becomes 1.

Now left=2, right=1, so loop ends.

Result is [1,4,2,3], which matches the example.

Another example: [5,5,5,5]. Sorted is same. So left starts at 0, right at 3.

Append 5 (left=0), left=1.

Append 5 (right=3), right=2.

Append 5 (left=1), left=2.

Append 5 (right=2), right=1.

So the list is [5,5,5,5], which is correct.

Another test case: empty list. So if lst is empty, return empty list.

So the code steps:

- Sort the list.
- If the list is empty, return it.
- Else, use two pointers to build the result.

Wait, but how to handle the case when the list has odd number of elements. Let's say [1,2,3]. Sorted is [1,2,3].

left=0, right=2.

Append 1 (left=0), left=1.

Append 3 (right=2), right=1.

Now left=1, right=1. So next, append lst[1] =2, left becomes 2. Then right is 0, so loop ends. So the result is [1,3,2], which is correct.

Yes, that seems to work.

So the code would be:

Sort the list.

Initialize left and right.

While left <= right:

   append lst[left], left +=1

   if left <= right: append lst[right], right -=1

Wait, but in the code, after appending the left, we need to check if left is still <= right before appending the right.

So for example, in the case of odd length, after taking the left, the left might be equal to right, so after taking left, left becomes right+1, so the next step would not append the right.

Wait, let's take [1,2,3].

After first append (1), left is 1. Then check if left (1) <= right (2) → yes. Append lst[2] (3), right becomes 1.

Now left is 1, right is 1. So next iteration: append lst[1] (2), left becomes 2. Then check if left (2) <= right (1) → no. So loop ends.

So the result is [1,3,2], which is correct.

So the code should handle that.

So the steps in code:

def strange_sort_list(lst):
    lst_sorted = sorted(lst)
    left = 0
    right = len(lst_sorted) - 1
    result = []
    while left <= right:
        result.append(lst_sorted[left])
        left += 1
        if left <= right:
            result.append(lst_sorted[right])
            right -= 1
    return result

Let me test this with the examples.

First example: [1,2,3,4] → sorted is [1,2,3,4].

left=0, right=3.

Append 1, left=1. Then append 4, right=2.

Append 2, left=2. Append 3, right=1.

Now left=2, right=1 → loop ends. So result is [1,4,2,3]. Correct.

Another example: [5,5,5,5]. Sorted same.

Append 5 (left=0 → left=1), append 5 (right=3 → right=2).

Append 5 (left=1 → left=2), append 5 (right=2 → right=1).

Result [5,5,5,5]. Correct.

Empty list: returns empty list. Correct.

Another test case: [1,3,2,4] → sorted [1,2,3,4], same as first example.

So the code should work.

Wait, but what about a list with one element? Like [5]. Then sorted is [5]. left=0, right=0.

Append 5, left becomes 1. Then check if left (1) <= right (0) → no. So return [5]. Correct.

Another test case: [1,2]. Sorted [1,2]. Append 1, left=1. Then append 2, right=0. So result [1,2]. Wait, but according to the problem statement, for [1,2], the strange sort should be [1,2], since after taking min (1), the remaining is [2], so max is 2. So yes, [1,2]. So the code would return [1,2], which is correct.

Wait, but according to the problem statement, the example given is [1,2,3,4] → [1,4,2,3]. So for two elements, it's [min, max], which is [1,2], which is correct.

So the code seems to handle all cases.

Now, check if the code is correct.

So the code should be:

def strange_sort_list(lst):
    sorted_lst = sorted(lst)
    left, right = 0, len(sorted_lst) - 1
    result = []
    while left <= right:
        result.append(sorted_lst[left])
        left += 1
        if left <= right:
            result.append(sorted_lst[right])
            right -= 1
    return result

Yes, that's the code.

Wait, but the problem says "return list in strange order. Strange sorting, is when you start with the minimum value, then maximum of the remaining integers, then minimum and so on."

So the code does exactly that.

So this should be the correct implementation.

Now, check if there are any edge cases.

Another edge case: list with two elements, [2,1]. Sorted becomes [1,2]. Then the code appends 1, then 2. So [1,2], which is correct.

Another case: [3, 1, 2]. Sorted [1,2,3]. The code would append 1, then 3, then 2. So [1,3,2], which is correct.

Yes.

So the code should be correct.

Now, the problem says to return the complete executable function with any needed imports. The only import needed is none, since sorted is a built-in function.

So the code is as written.

So the answer should be the code block with the function.
</think>

def strange_sort_list(lst):
    sorted_lst = sorted(lst)
    left, right = 0, len(sorted_lst) - 1
    result = []
    while left <= right:
        result.append(sorted_lst[left])
        left += 1
        if left <= right:
            result.append(sorted_lst[right])
            right -= 1
    return result

def check(candidate):

    # Check some simple cases
    assert candidate([1, 2, 3, 4]) == [1, 4, 2, 3]
    assert candidate([5, 6, 7, 8, 9]) == [5, 9, 6, 8, 7]
    assert candidate([1, 2, 3, 4, 5]) == [1, 5, 2, 4, 3]
    assert candidate([5, 6, 7, 8, 9, 1]) == [1, 9, 5, 8, 6, 7]
    assert candidate([5, 5, 5, 5]) == [5, 5, 5, 5]
    assert candidate([]) == []
    assert candidate([1,2,3,4,5,6,7,8]) == [1, 8, 2, 7, 3, 6, 4, 5]
    assert candidate([0,2,2,2,5,5,-5,-5]) == [-5, 5, -5, 5, 0, 2, 2, 2]
    assert candidate([111111]) == [111111]

    # Check some edge cases that are easy to work out by hand.
    assert True


check(strange_sort_list)

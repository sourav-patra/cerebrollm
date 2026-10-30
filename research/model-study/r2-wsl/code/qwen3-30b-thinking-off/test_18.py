Okay, let's see. I need to implement a function that finds the two closest numbers in a list and returns them as a tuple with the smaller first.

Hmm, the problem says the list has at least two elements. So first, maybe I should sort the list. Because if the list is sorted, the closest elements would be adjacent to each other. Like, in a sorted list, the minimum difference between any two elements must be between two consecutive elements. That makes sense because if they weren't consecutive, there would be a smaller difference between some other pair.

So the plan is: sort the list, then iterate through the sorted list, calculate the difference between each consecutive pair, and keep track of the pair with the smallest difference.

Wait, but what if there are duplicates? Like in the example where the input is [1.0, 2.0, 3.0, 4.0, 5.0, 2.0], the output is (2.0, 2.0). So when there are two same numbers, their difference is zero, which is the smallest possible. So the function should handle that.

So steps:

1. Sort the list. Let's say the sorted list is [a, b, c, ...], where a <= b <= c etc.

2. Iterate through the sorted list from index 0 to len-2, compute the difference between numbers[i+1] and numbers[i].

3. Track the minimum difference and the corresponding pair.

Wait, but the problem says to return the pair in order (smaller, larger). Since the list is sorted, the pair will naturally be (numbers[i], numbers[i+1]) because numbers[i] <= numbers[i+1].

So for example, if the sorted list is [1, 2, 2.2, 3], then the closest pair is 2 and 2.2, which are consecutive in the sorted list.

Another example: if the list is [2.0, 2.0], then the sorted list is [2.0, 2.0], and the difference is zero.

So the algorithm would be:

- Sort the numbers.

- Initialize min_diff to a large value, and closest_pair to (0,0).

- Loop through i from 0 to len(numbers)-2:

   current_diff = numbers[i+1] - numbers[i]

   if current_diff < min_diff:

      min_diff = current_diff

      closest_pair = (numbers[i], numbers[i+1])

- Return closest_pair.

Wait, but what if there are multiple pairs with the same minimal difference? The problem says "select and return two that are the closest". So any such pair would be acceptable, but since the list is sorted, the first occurrence would be the one we find. But the problem examples don't have such cases, but the function should return the first pair with the minimal difference. Wait, but in the example where there are two pairs with same difference, like [1, 2, 3, 4], the closest is 1-2, 2-3, etc. But the minimal difference is 1 between 1-2, 2-3, etc. So the first pair would be (1,2), but maybe the problem expects the first occurrence. However, the problem statement says "select and return two that are the closest", so any such pair is acceptable. So the algorithm as described would work.

Now, let's test with the examples.

First example: [1.0, 2.0, 3.0, 4.0, 5.0, 2.2]

Sort the list: [1.0, 2.0, 2.2, 3.0, 4.0, 5.0]

Check consecutive differences:

2.0 -1.0 = 1.0

2.2 -2.0 = 0.2

3.0-2.2=0.8, etc. So the smallest is 0.2, so the pair is (2.0, 2.2), which matches the example.

Second example: [1.0, 2.0, 3.0, 4.0, 5.0, 2.0]

Sort: [1.0, 2.0, 2.0, 3.0, 4.0, 5.0]

Consecutive differences: 1.0, 0.0, 1.0, etc. So the smallest is 0.0 between 2.0 and 2.0. So the pair is (2.0, 2.0), which matches the example.

So the algorithm seems correct.

Now, code-wise, need to sort the list. Then loop through.

But what about the case where the list has exactly two elements? Well, the problem states the list has at least two elements, so the loop will run once.

So the code:

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    sorted_nums = sorted(numbers)
    min_diff = float('inf')
    closest_pair = (0, 0)
    for i in range(len(sorted_nums) - 1):
        diff = sorted_nums[i+1] - sorted_nums[i]
        if diff < min_diff:
            min_diff = diff
            closest_pair = (sorted_nums[i], sorted_nums[i+1])
    return closest_pair

Wait, but in Python, when you sort a list of floats, it's straightforward. So this should work.

Wait, but let's check for the case where the minimal difference is between two elements that are not the first occurrence. For example, if the list is [1, 3, 5, 6], sorted is [1,3,5,6]. The differences are 2, 2, 1. So the minimal is 1 between 5 and 6. So the code would correctly return (5,6).

Another test case: [1.5, 1.0, 2.0]. Sorted is [1.0, 1.5, 2.0]. Differences are 0.5 and 0.5. So the first pair (1.0, 1.5) would be chosen. But the problem says "select and return two that are the closest", so either pair is acceptable. The code returns the first occurrence, which is correct.

So the code should work.

Now, check if the code handles the case where the minimal difference is zero. Like [2.0, 2.0], which would sort to [2.0, 2.0], and the difference is zero, so the pair is (2.0, 2.0).

Yes.

So the code seems correct.

Now, need to make sure that the function is correctly implemented with the right imports. The problem says to include any needed imports. The function uses List and Tuple from typing, so the imports are already given in the problem statement. Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

Wait, the user provided the code with from typing import List, Tuple. So the code should include that. Wait, the problem's code block starts with that import. So the code I write should include that, but since the user's example already has it, but in the problem statement, the code block starts with that. Wait, the user provided the code as:

from typing import List, Tuple

def find_closest_elements(...)

So the code I need to write should include that import. Wait, but the user's instruction says "Implement the Python function below. Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should include the import, which is already part of the problem's code. So the code I provide should have the import and the function.

Wait, the problem's code block starts with the import, so the answer should include that.

So the code I need to write is:

from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    sorted_nums = sorted(numbers)
    min_diff = float('inf')
    closest_pair = (0.0, 0.0)
    for i in range(len(sorted_nums) - 1):
        diff = sorted_nums[i+1] - sorted_nums[i]
        if diff < min_diff:
            min_diff = diff
            closest_pair = (sorted_nums[i], sorted_nums[i+1])
    return closest_pair

Wait, but in the code, the initial closest_pair is set to (0,0), but maybe it's better to initialize it to the first pair. Wait, but the list has at least two elements, so the loop will run at least once. So the initial min_diff is infinity, and the first pair will be set. So the code is okay.

Wait, but in the code, the initial closest_pair is (0,0), but if the list is [1,2], then the code would set closest_pair to (1,2), which is correct. So the initial value is overwritten.

Yes, because the loop runs for i in 0 to len-2, which for len=2, i=0. So the code will process the first pair.

So the code is correct.

Another edge case: list with two elements. For example, [5.0, 3.0]. Sorted becomes [3.0,5.0], difference is 2.0, so return (3.0,5.0).

Yes.

So the code should work.

Now, check if the code is correctly written. Let's see.

Wait, in Python, when you sort a list, it's in ascending order, so the consecutive elements are in order. So the code is correct.

So the code should be as written.

I think that's it. So the final code is as above.
</think>

from typing import List, Tuple

def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    sorted_nums = sorted(numbers)
    min_diff = float('inf')
    closest_pair = (0.0, 0.0)
    for i in range(len(sorted_nums) - 1):
        diff = sorted_nums[i+1] - sorted_nums[i]
        if diff < min_diff:
            min_diff = diff
            closest_pair = (sorted_nums[i], sorted_nums[i+1])
    return closest_pair



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2]) == (3.9, 4.0)
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0]) == (5.0, 5.9)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.2]) == (2.0, 2.2)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0]) == (2.0, 2.0)
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1]) == (2.2, 3.1)


check(find_closest_elements)

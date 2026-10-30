Okay, let's see. I need to implement a function that rescales a list of numbers to the unit interval [0,1]. The smallest number becomes 0 and the largest becomes 1. So first, I should find the minimum and maximum values in the list.

Wait, the problem says the list has at least two elements, so min and max will be different. Otherwise, if all elements are the same, but the problem states at least two elements, but maybe they could be same? Wait, no, the problem says "apply a linear transform such that the smallest becomes 0 and largest becomes 1". So if all elements are the same, min equals max, which would cause division by zero. But the problem states the list has at least two elements. Wait, but maybe the problem assumes that there are at least two distinct elements. Hmm, but the problem statement says "list of numbers (of at least two elements)", but doesn't specify they are distinct. However, the example given has distinct numbers.

But the problem says "the smallest number will become 0 and the largest will become 1". So if all numbers are the same, then min and max are equal, and the transformation would be undefined. But the problem probably assumes that there are at least two different numbers. So in the code, I can proceed under the assumption that min != max.

So steps: find min and max of the list. Then for each number x in the list, compute (x - min) / (max - min). That should give the rescaled value.

Let me test with the example. The example input is [1.0, 2.0, 3.0, 4.0, 5.0]. Min is 1, max is 5. So for 1.0: (1-1)/(5-1) = 0/4 = 0.0. For 2.0: (2-1)/4 = 0.25. Which matches the example. So that's correct.

So the code should compute min_val = min(numbers), max_val = max(numbers). Then for each x in numbers, (x - min_val) / (max_val - min_val).

Wait, but need to handle the case where max_val - min_val is zero. But the problem states that the list has at least two elements. However, if all elements are the same, then max_val - min_val is zero, which would cause division by zero. But the problem says "apply a linear transform such that the smallest becomes 0 and largest becomes 1". If all elements are the same, then the smallest and largest are the same, so the transformation would require 0 and 1 to be the same, which is impossible. So the problem probably assumes that there are at least two distinct elements. So the code can proceed without handling that case, as per the problem's constraints.

So the code would be:

def rescale_to_unit(numbers: List[float]) -> List[float]:
    min_val = min(numbers)
    max_val = max(numbers)
    range_val = max_val - min_val
    return [(x - min_val) / range_val for x in numbers]

Wait, but let's check the example. For [1,2,3,4,5], min is 1, max is 5, range is 4. So each element minus 1 divided by 4. So 0, 0.25, 0.5, 0.75, 1.0. Which matches the example.

Another test case: [0, 0, 0] would be invalid, but the problem states at least two elements, but if they are same, but the problem says "list of numbers (of at least two elements)", but the problem's example has distinct. So the code can assume that min and max are different.

So the code should be correct.

Now, check if the code is correct. Let's see.

Yes, the code computes min and max, then scales each element.

So the function should be as written.

Now, check if any imports are needed. The function uses List from typing, so the import is already given. So the code should include the import.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should have the import statement for List.

Wait, the user provided the code with from typing import List, so the code should include that.

Wait, the user's code block starts with:

from typing import List

def rescale_to_unit(...)

So the code should include that import.

So the complete code is:

from typing import List

def rescale_to_unit(numbers: List[float]) -> List[float]:
    min_val = min(numbers)
    max_val = max(numbers)
    range_val = max_val - min_val
    return [(x - min_val) / range_val for x in numbers]

Wait, but in Python, division of floats is okay. So this should work.

Testing with the example:

numbers = [1.0, 2.0, 3.0, 4.0, 5.0]

min_val = 1.0, max_val =5.0, range_val=4.0.

Each element:

1.0: (1-1)/4 = 0.0

2.0: 1/4 = 0.25

Yes, correct.

Another test case: [10, 20], should return [0.0, 1.0].

Yes.

Another test case: [5, 10, 15], min 5, max 15, range 10. So 5 becomes 0, 10 becomes 0.5, 15 becomes 1.0.

Yes.

So the code should be correct.

So the answer is the code as written.
</think>

from typing import List


def rescale_to_unit(numbers: List[float]) -> List[float]:
    min_val = min(numbers)
    max_val = max(numbers)
    range_val = max_val - min_val
    return [(x - min_val) / range_val for x in numbers]



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([2.0, 49.9]) == [0.0, 1.0]
    assert candidate([100.0, 49.9]) == [1.0, 0.0]
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0]) == [0.0, 0.25, 0.5, 0.75, 1.0]
    assert candidate([2.0, 1.0, 5.0, 3.0, 4.0]) == [0.25, 0.0, 1.0, 0.5, 0.75]
    assert candidate([12.0, 11.0, 15.0, 13.0, 14.0]) == [0.25, 0.0, 1.0, 0.5, 0.75]

check(rescale_to_unit)

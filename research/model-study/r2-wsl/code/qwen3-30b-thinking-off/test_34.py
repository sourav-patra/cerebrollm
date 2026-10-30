Okay, let's see. I need to implement a function called rolling_max that takes a list of integers and returns a list where each element is the maximum up to that point in the sequence.

Hmm, so for example, the input [1, 2, 3, 2, 3, 4, 2] should give [1, 2, 3, 3, 3, 4, 4]. Let me think about how to approach this.

The key here is that for each position i in the input list, the output at i should be the maximum of all elements from the start up to i. So for the first element, it's just the first number. Then for the second, it's the max of the first two, and so on.

So, the straightforward way would be to iterate through the list, keeping track of the current maximum. For each element, compare it with the current max, update if necessary, and add to the result list.

Let me test this logic with the example. Starting with numbers = [1,2,3,2,3,4,2].

Initialize current_max as -infinity or the first element. Wait, the first element is 1, so current_max starts at 1. The first output is 1.

Next element is 2. Current max is 1, so new max is 2. Output now [1,2].

Third element 3: current max 2, so new max 3. Output [1,2,3].

Fourth element 2: current max is 3, so output 3. So the list becomes [1,2,3,3].

Fifth element 3: current max is 3, so output remains 3. So [1,2,3,3,3].

Sixth element 4: current max 3, so new max 4. Output adds 4.

Seventh element 2: current max is 4, so output is 4. So the final list is [1,2,3,3,3,4,4], which matches the example.

So the algorithm is: initialize an empty list for the result, and a variable to track the current maximum. For each number in the input list, compare it with the current max. If the number is larger, update the current max. Then append the current max to the result list.

Wait, but what if the list is empty? The problem statement says "from a given list of integers", so maybe we can assume the list is not empty. But the problem example has a non-empty list. However, to be safe, maybe handle the empty list case. But the problem's example doesn't mention it, so perhaps the input will always have at least one element. Let's proceed under that assumption.

So the code steps:

- Initialize current_max to the first element, or maybe start with the first element.

Wait, for the first element, the rolling max is the element itself. So for the first element, the current max is numbers[0], then for each subsequent element, compare with current_max.

So the code could be:

result = []
current_max = None

But for the first element, current_max would be set to numbers[0], then append to result.

Wait, let's code it step by step.

Initialize current_max as the first element. Then for each number in the list, if the number is greater than current_max, update current_max. Then append current_max to the result.

Wait, but for the first element, current_max is numbers[0], so the first element of the result is numbers[0].

Yes.

So for the input [1,2,3,2,3,4,2], the code would process each element:

i=0: current_max = 1, result = [1]

i=1: 2 > 1 → current_max=2, result [1,2]

i=2: 3>2 → current_max=3, result [1,2,3]

i=3: 2 <3 → current_max remains 3, result appends 3.

And so on.

So the code can be written as:

def rolling_max(numbers: List[int]) -> List[int]:
    if not numbers:
        return []
    result = []
    current_max = numbers[0]
    for num in numbers:
        if num > current_max:
            current_max = num
        result.append(current_max)
    return result

Wait, but let's check for the first element. The first element is processed, current_max is set to numbers[0], then for each num in numbers, which includes the first element. Wait, no. Wait, the loop is for each num in numbers. So for the first element, num is 1. current_max is numbers[0] (1), so num (1) is not greater than current_max (1), so current_max remains 1, and append to result. So the first element is correctly added.

Wait, but in the code above, current_max is initialized to numbers[0], then the loop starts. So for the first element, num is numbers[0], and since num is not greater than current_max (they are equal), current_max stays the same, and we append current_max. So the first element is correctly added.

Yes, that's correct.

Testing with the example:

numbers = [1,2,3,2,3,4,2]

current_max starts at 1.

Loop through each num:

num=1: 1 <=1 → current_max remains 1. Append 1 → result [1]

num=2: 2>1 → current_max=2. Append 2 → [1,2]

num=3: 3>2 → current_max=3. Append 3 → [1,2,3]

num=2: 2<3 → append 3 → [1,2,3,3]

num=3: 3==3 → append 3 → [1,2,3,3,3]

num=4: 4>3 → current_max=4. Append 4 → [1,2,3,3,3,4]

num=2: append 4 → [1,2,3,3,3,4,4]

Which matches the example.

So the code should work.

Now, check for edge cases. What if all elements are the same? Like [5,5,5]. The output should be [5,5,5].

Another edge case: decreasing list, like [5,4,3,2,1]. Output should be [5,5,5,5,5].

Another case: empty list. The problem says "from a given list of integers", but the function should handle empty list. The problem's example doesn't show it, but according to the code, if numbers is empty, the function returns [].

So the code as written handles that.

Now, check if the code is correct.

Yes, the code seems correct.

Now, the problem says to return the complete executable function with any needed imports. The function uses List from typing, so we need to import List.

Wait, the function signature is:

from typing import List, Tuple

def rolling_max(numbers: List[int]) -> List[int]:

So the import is already provided. Wait, the user provided the code with the imports. Wait, the user's code block starts with:

from typing import List, Tuple

def rolling_max(...)

So in the code we need to write, we need to include the imports. Wait, but the user's instruction says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should include the import statements. Wait, but the user's example code already has the import. Wait, the user provided the code as:

from typing import List, Tuple

def rolling_max(...)

So in the answer, we need to include that import, and the function.

Wait, but the problem says "Implement the Python function below. Return the complete executable function with any needed imports..."

So the code should have the import statements. So the code block should start with the imports, then the function.

Wait, but the user's example code already includes the import. So the answer should include that import, and the function.

Wait, the user's code block shows:

from typing import List, Tuple

def rolling_max(...)

So the answer should have that, and the function body.

So the code to return is:

from typing import List, Tuple

def rolling_max(numbers: List[int]) -> List[int]:
    if not numbers:
        return []
    result = []
    current_max = numbers[0]
    for num in numbers:
        if num > current_max:
            current_max = num
        result.append(current_max)
    return result

Wait, but let's check if the code is correct. Let's test with the example.

Yes, as we did before.

Another possible optimization: instead of checking if the list is empty, but since the problem's example has a non-empty list, but the code should handle empty lists. The code as written returns [] for empty input, which is correct.

So this should be the correct implementation.

Wait, but the problem says "from a given list of integers", so maybe the input is non-empty, but the code should handle empty lists as well. So the check for empty list is good.

Another way to write it without the empty check: if the list is empty, the loop won't run, but the code would have current_max = numbers[0], which would throw an error. So the empty check is necessary.

Yes, so the code as written is correct.

So the final code should be as above.
</think>

from typing import List, Tuple

def rolling_max(numbers: List[int]) -> List[int]:
    if not numbers:
        return []
    result = []
    current_max = numbers[0]
    for num in numbers:
        if num > current_max:
            current_max = num
        result.append(current_max)
    return result



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == []
    assert candidate([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert candidate([4, 3, 2, 1]) == [4, 4, 4, 4]
    assert candidate([3, 2, 3, 100, 3]) == [3, 3, 3, 100, 100]

check(rolling_max)

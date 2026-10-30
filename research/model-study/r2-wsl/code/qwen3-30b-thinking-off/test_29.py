Okay, let's see. I need to implement a function called common that takes two lists, l1 and l2, and returns the sorted list of unique common elements.

Hmm, so first, I need to find elements that are present in both lists. But they have to be unique, so duplicates in either list shouldn't matter. For example, if l1 has [1, 1, 2] and l2 has [1, 3], the common elements should be [1], not [1,1].

So the steps would be: find the intersection of the two lists, remove duplicates, then sort the result.

Wait, but how to handle duplicates. Using sets would automatically remove duplicates. So converting both lists to sets, taking the intersection, then converting back to a list and sorting.

Let me think. For example, l1 = [1, 4, 3, 34, 653, 2, 5], l2 = [5, 7, 1, 5, 9, 653, 121]. The common elements are 1, 5, 653. So converting both to sets: set(l1) is {1,2,3,4,5,34,653}, set(l2) is {1,5,7,9,653,121}. The intersection is {1,5,653}, then sorted would be [1,5,653], which matches the example.

Another example: l1 = [5,3,2,8], l2 = [3,2]. The intersection is {2,3}, sorted is [2,3], which matches the second example.

So the function should convert both lists to sets, find the intersection, convert that to a list, sort it, and return.

Wait, but the problem says "sorted unique common elements". So the intersection of the two sets will give the unique elements common to both. Then sorting them.

So the code would be:

def common(l1, l2):
    return sorted(set(l1) & set(l2))

Wait, but let me check. The & operator for sets is the intersection. So set(l1) & set(l2) gives the common elements. Then sorted converts it to a sorted list.

Yes, that should work.

Testing the examples:

First example: set(l1) is {1,2,3,4,5,34,653}, set(l2) is {1,5,7,9,653,121}. Intersection is {1,5,653}, sorted is [1,5,653].

Second example: set(l1) is {2,3,5,8}, set(l2) is {2,3}, intersection {2,3}, sorted [2,3].

Yes, that's correct.

So the function is straightforward. Now, need to make sure that the code is correct.

Wait, the problem says "Return sorted unique common elements for two lists." So the code should return the sorted list.

So the code would be:

def common(l1, l2):
    return sorted(set(l1) & set(l2))

But wait, in Python, the & operator for sets is the intersection. So yes.

Let me check if there's any edge cases. For example, if there are no common elements, it should return an empty list. Like common([1,2], [3,4]) returns [].

Yes, because set(l1) & set(l2) would be empty, sorted([]) is [].

Another edge case: empty lists. If both are empty, returns [].

So the code should handle that.

So the code seems correct.

Now, the problem says to return the complete executable function with any needed imports. But in this case, no imports are needed because sets are built-in.

So the code is:

def common(l1: list, l2: list):
    return sorted(set(l1) & set(l2))

Wait, but the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So I need to write the code as is, with the function definition.

Wait, the function signature uses type hints: l1: list, l2: list. But in Python, for type hints, you might need to import List from typing, but the problem says "without explanations" and just return the code.

Wait, but the problem's example code uses list in the type hints. However, in Python 3.9+, list is a built-in type, so you don't need to import it. But if the code is written for older versions, you might need to import List from typing. However, the problem says "Implement the Python function below", and the example uses list as a type hint, so probably assuming Python 3.9+ where list is a built-in type.

So the code can be written without importing anything.

Therefore, the correct code is as above.

Wait, but let me check. The problem's example code shows:

def common(l1: list, l2: list):

So the type hints are using list, which is a built-in type in Python 3.9 and above. So no need for imports.

Therefore, the code is correct as written.

So the final code should be:

def common(l1: list, l2: list):
    return sorted(set(l1) & set(l2))

Yes, that's it.
</think>

def common(l1: list, l2: list):
    return sorted(set(l1) & set(l2))



METADATA = {}


def check(candidate):
    assert candidate([1, 4, 3, 34, 653, 2, 5], [5, 7, 1, 5, 9, 653, 121]) == [1, 5, 653]
    assert candidate([5, 3, 2, 8], [3, 2]) == [2, 3]
    assert candidate([4, 3, 2, 8], [3, 2, 4]) == [2, 3, 4]
    assert candidate([4, 3, 2, 8], []) == []


check(common)

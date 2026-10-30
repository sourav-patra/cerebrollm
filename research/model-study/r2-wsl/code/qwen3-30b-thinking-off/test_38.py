We are going to sort the list and then find the second smallest.
 However, note that there might be duplicates. We want the second smallest distinct value?
 But the problem says: "the 2nd smallest element", meaning if there are duplicates, we might have to skip duplicates?
 Let's read the examples: 
   next_smallest([1, 1]) == None -> because there is no second smallest distinct element? 
   But note: the list [1, 1] has two elements, both 1. The smallest is 1, and there is no element that is greater than 1 and less than or equal to the next? 
   Actually, the problem says: "Return None if there is no such element."

 Approach:
   We can sort the list and then traverse to find the first element that is greater than the smallest.

 Steps:
   If the list has less than 2 elements, return None.
   Sort the list.
   Let min_val = lst[0]
   Then traverse from the second element until we find an element that is greater than min_val.
   If we find one, that's the second smallest.
   If we don't (meaning all elements are the same), return None.

 However, note: the example [5, 1, 4, 3, 2] -> sorted becomes [1,2,3,4,5] -> second smallest is 2.

 But what about [1, 1, 2, 3]? 
   The smallest is 1, the next smallest (distinct) is 2. But note: the problem says "element", meaning the value? 
   The example [1,1] returns None, so we are to consider distinct? Actually, the problem does not specify distinct, but the example [1,1] returns None.

 However, note: the problem says "the 2nd smallest element", meaning the element that is the second smallest in the list (if we consider duplicates as separate, then the second smallest element in [1,1,2] would be 1? but that's the same as the smallest). 

 But the example [1,1] returns None, so we are to return the second smallest distinct value? Or the second smallest in the sorted order (which would be the second element in the sorted list, but if there are duplicates, then the second element might be the same as the first).

 Actually, the problem says: "the 2nd smallest element of the list". In a list, the smallest element is the first when sorted, and the second smallest is the next one that is not equal to the smallest? 

 Let me check the examples: 
   [1, 2, 3, 4, 5] -> sorted: [1,2,3,4,5] -> second smallest is 2 (the element at index 1).
   [5, 1, 4, 3, 2] -> sorted: [1,2,3,4,5] -> second smallest is 2.

   [1,1] -> sorted: [1,1] -> the second element is 1, but that is the same as the smallest. So we don't want that? The problem says "2nd smallest", meaning the next distinct value? 

 However, the problem does not say "distinct". But the example [1,1] returns None, so we must skip duplicates.

 Therefore, we can do:
   Sort the list.
   Traverse the sorted list to find the first element that is greater than the first element.

   Steps:
      if len(lst) < 2: return None
      sorted_lst = sorted(lst)
      smallest = sorted_lst[0]
      for i in range(1, len(sorted_lst)):
          if sorted_lst[i] > smallest:
              return sorted_lst[i]
      return None   # because we didn't find any element greater than smallest

 But note: what if the list has negative numbers? The same logic applies.

 Example: [1, 1, 1, 2] -> sorted: [1,1,1,2] -> smallest=1, then we find 2 at index 3 -> return 2.

 However, the problem says "2nd smallest element", and in the list [1,1,1,2], the smallest is 1, and the next smallest (the second smallest distinct) is 2. But note: the problem does not say "distinct", but the example [1,1] returns None, meaning that we are to consider the second smallest distinct value? Actually, the problem statement is ambiguous.

 But the examples provided:
   next_smallest([1, 1]) == None

 So we are to return the second smallest distinct value? Or the second element in the sorted list that is not equal to the smallest? 

 Actually, the problem says: "the 2nd smallest element", meaning the element that is the second smallest in the entire list (if we list the elements in increasing order, the second one). However, in [1,1,2], the sorted list is [1,1,2]. The smallest element is 1 (at index0), the next element (index1) is also 1, so the second smallest element is 1? But then why would [1,1] return None? Because in [1,1] there is no second element that is greater than the smallest? 

 However, the problem says: "Return None if there is no such element." meaning if there is no second smallest element (which would be the case when there are less than two distinct values?).

 But note: the problem does not say "distinct", so the second smallest element in [1,1] is 1 (the element at index1). However, the example says next_smallest([1,1]) == None.

 Therefore, the problem must mean: the second smallest distinct element.

 So we are to find the second smallest distinct value.

 How about: 
   We can convert the list to a set to get distinct values, then sort the set and take the second element? But note: if there is only one distinct value, then we return None.

 Steps for distinct:
   distinct = sorted(set(lst))
   if len(distinct) < 2:
        return None
   else:
        return distinct[1]

 However, let's test with the examples:
   [1,2,3,4,5] -> distinct = [1,2,3,4,5] -> distinct[1] = 2 -> correct.
   [5,1,4,3,2] -> distinct = [1,2,3,4,5] -> distinct[1]=2 -> correct.
   [] -> set is empty -> len<2 -> None -> correct.
   [1,1] -> distinct = [1] -> len=1 -> None -> correct.

 But note: the problem says "element", and the distinct set approach is standard for "second smallest distinct".

 However, the problem does not say "distinct", but the examples require it.

 So we'll go with the distinct set method.

 But note: the problem says "element", and in the list [1,1,2], the distinct set is [1,2] so the second smallest distinct is 2. However, the problem might be interpreted as: the second smallest element in the list (which would be the second element in the sorted list, which is 1 for [1,1,2]). But the example [1,1] returns None, so that interpretation would have [1,1] returning 1 (the second element) but the example says None.

 Therefore, the intended meaning is the second smallest distinct value.

 So we'll implement using set.

 However, note: the problem does not require the distinct set to be sorted in the order of appearance, but we are sorting the distinct set.

 Let's write the code accordingly.

 But note: the problem says "list of integers", so set is safe.

 Code:

   if len(lst) < 2:
        return None
   distinct = sorted(set(lst))
   if len(distinct) < 2:
        return None
   return distinct[1]

 However, we can do without the explicit length check for the set because if the set has less than 2, then distinct[1] would be out of range.

 Alternatively, we can do:

   distinct = sorted(set(lst))
   return distinct[1] if len(distinct) >= 2 else None

 But note: the problem says "Return None if there is no such element", meaning if there are less than two distinct elements.

 However, the problem also says: "the 2nd smallest element", so if there are two distinct elements, then the second smallest distinct element is the one we want.

 But note: the set might have more than two, but we only need the second smallest.

 So the above code is efficient enough for the problem.

 However, the problem does not specify the size of the list, but it's acceptable.

 Let's write the function accordingly.

 But note: the problem says "Return the complete executable function with any needed imports".

 We don't need any imports for set and sorted.

 So the function:

   def next_smallest(lst):
        if len(lst) < 2:
            return None
        distinct = sorted(set(lst))
        if len(distinct) < 2:
            return None
        return distinct[1]

 However, we can combine the conditions:

   distinct = sorted(set(lst))
   return distinct[1] if len(distinct) >= 2 else None

 But note: the problem says "Return None if there is no such element", and the condition for no such element is when there are less than two distinct elements.

 Alternatively, we can write:

   distinct = sorted(set(lst))
   if len(distinct) < 2:
        return None
   return distinct[1]

 We'll write it in a concise way.

 However, note: the problem says "the 2nd smallest", meaning the second element in the sorted distinct list (which is the second smallest distinct value).

 Let's test with the provided examples.

 But note: the problem says "next_smallest([1, 2, 3, 4, 5]) == 2", and our function returns 2.

 However, what if the list has negative numbers? 
   Example: [0, -1, -2] -> distinct = sorted(set([0,-1,-2])) = [-2,-1,0] -> distinct[1] = -1 -> which is the second smallest.

 So it's correct.

 Now, write the function.

 Important: We must return the complete function in one code block.

 Let's write it.
</think>

def next_smallest(lst):
    distinct = sorted(set(lst))
    if len(distinct) < 2:
        return None
    return distinct[1]

def check(candidate):

    # Check some simple cases
    assert candidate([1, 2, 3, 4, 5]) == 2
    assert candidate([5, 1, 4, 3, 2]) == 2
    assert candidate([]) == None
    assert candidate([1, 1]) == None
    assert candidate([1,1,1,1,0]) == 1
    assert candidate([1, 0**0]) == None
    assert candidate([-35, 34, 12, -45]) == -35

    # Check some edge cases that are easy to work out by hand.
    assert True


check(next_smallest)

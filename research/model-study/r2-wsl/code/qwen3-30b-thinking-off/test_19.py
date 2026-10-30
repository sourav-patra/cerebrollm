We are counting the number of elements in the array for which the sum of the digits (with the sign of the first digit for negative numbers) is greater than 0.
 Steps:
 1. For each number in the array:
    - Convert the number to a string to process each digit, but note: negative numbers have a minus sign at the beginning.
 2. We can handle negative numbers by:
    - If the number is negative, we can take the absolute value and then adjust the first digit to be negative? 
      But note: the problem says "signed digits", meaning for -123, the digits are -1, 2, 3.
 3. Alternatively, we can process the string representation:
    - For a negative number, the first character is '-' and then the rest are digits. We can take the first digit (after the minus) and make it negative, and then the rest positive.
    - However, note: the problem says "signed digits", so for -123: 
          digits: -1, 2, 3 -> sum = -1+2+3 = 4 > 0 -> so it would count.

 4. But note: what about a negative number that has a digit sum that is negative? For example, -1: 
        digits: -1 -> sum = -1 -> not counted.

 5. Approach for a number n:
    - If n is negative, we can convert to string and skip the minus sign for the first digit? Actually, we can do:
        s = str(n)
        if s[0] == '-':
            # then the first digit (which is the next character) is negative, and the rest are positive.
            # so we can take the rest of the string (without the minus) and then make the first digit negative.
            # Example: n = -123 -> s = "-123"
            # We can split: the first digit is '1' (which we will make negative) and then '2','3'
            # So: digits = [ -int(s[1]), int(s[2]), int(s[3]) ]? But note: the string might have more than 3 digits.

    - Alternatively, we can do:
        total = 0
        s = str(n)
        if s[0] == '-':
            # process the rest of the string, but the first digit (after minus) is negative
            for i, char in enumerate(s[1:]):
                digit = int(char)
                if i == 0:
                    total -= digit
                else:
                    total += digit
        else:
            for char in s:
                total += int(char)

 6. However, note: the problem says "If a number is negative, then its first signed digit will be negative". 
    So for -123, the first digit (which is 1) is taken as negative, and the rest as positive.

 7. But note: what about numbers with more than one digit? The above loop for negative numbers: 
        s = "-123" -> s[1:] = "123"
        i=0: digit=1 -> total = -1
        i=1: digit=2 -> total = -1+2 = 1
        i=2: digit=3 -> total = 1+3 = 4 -> which is >0.

 8. However, we can also do without a loop for each number by using a more efficient method.

 9. But note: the problem says "sum of digits" with the sign for the first digit of a negative number.

 10. Let's write a helper function to compute the digit sum for a single number.

 However, the problem is small (array of integers, and each integer has at most 10-20 digits), so we can do the string conversion.

 11. We'll create a helper function inside count_nums? Or we can do it inline.

 12. Alternatively, we can do:

        def digit_sum(n):
            if n == 0:
                return 0
            s = str(n)
            if s[0] == '-':
                # Process the negative number
                total = 0
                # The first digit (after the minus) is negative, the rest positive.
                # We can split the string without the minus
                num_str = s[1:]
                # The first character of num_str is the first digit (which we make negative)
                total = -int(num_str[0])
                for i in range(1, len(num_str)):
                    total += int(num_str[i])
                return total
            else:
                return sum(int(d) for d in s)

 13. But note: what about positive numbers? They are straightforward.

 14. However, note: the problem says "If a number is negative", so positive numbers are handled without the minus.

 15. But wait: what about zero? 
        The problem says: "sum of digits > 0", so zero would not count.
        For zero: 
            str(0) -> "0", so the sum is 0 -> not counted.

 16. However, note: the problem states that the array can have negative numbers and positive numbers.

 17. Let's test with the examples:

      Example 1: count_nums([]) -> 0 (correct)

      Example 2: count_nums([-1, 11, -11])
          -1: 
              s = "-1" -> num_str = "1", total = -1 -> sum = -1 -> not counted.
          11: 
              s = "11" -> sum = 1+1 = 2 -> counted.
          -11:
              s = "-11" -> num_str = "11", total = -1 + 1 = 0 -> not counted.
          So total count = 1 -> matches.

      Example 3: count_nums([1, 1, 2]) 
          1: 1 -> counted
          1: 1 -> counted
          2: 2 -> counted
          total = 3 -> matches.

 18. However, note: the example [-1, 11, -11] returns 1, which matches.

 19. But wait: what about a negative number that has a positive digit sum? 
        Example: -12 -> 
            s = "-12" -> num_str = "12", total = -1 + 2 = 1 -> positive -> counted.

 20. So we'll write the helper function as described.

 21. However, note: the problem does not require a helper function, so we can do it inline.

 22. We'll iterate over the array, for each number compute the digit sum as described, and count if the sum > 0.

 23. But note: the problem says "sum of digits > 0", so we are counting the numbers for which the digit sum is strictly greater than 0.

 24. Let's code accordingly.

 25. Edge: empty array -> 0.

 26. We'll write:

        count = 0
        for num in arr:
            s = str(num)
            if s[0] == '-':
                # Process negative number
                # Skip the minus sign
                num_str = s[1:]
                # If the number is negative, the first digit (of the absolute value) is negative
                total = -int(num_str[0])
                for i in range(1, len(num_str)):
                    total += int(num_str[i])
                if total > 0:
                    count += 1
            else:
                total = sum(int(d) for d in s)
                if total > 0:
                    count += 1

 27. However, note: what if the number is 0? 
        str(0) -> "0", so in the else branch: total = 0 -> not counted. Correct.

 28. But what about negative zero? In Python, there is no negative zero for integers. So we are safe.

 29. Let's test with a few more examples:

      Example: [0] -> 0 (not counted) -> correct.
      Example: [-10] -> 
          s = "-10" -> num_str = "10"
          total = -1 + 0 = -1 -> not counted.

      Example: [-100] -> 
          total = -1 + 0 + 0 = -1 -> not counted.

      Example: [-12] -> -1+2 = 1 -> counted.

 30. But note: the problem says "first signed digit" meaning the first digit of the absolute value is taken as negative. 
      So for -12, the first digit (1) is negative, and the rest (2) is positive.

 31. However, note: the example -11: 
          -1 + 1 = 0 -> not counted.

 32. Now, let's write the code accordingly.

 33. We can also avoid the inner loop by using:

        total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])

 34. But note: if the number is negative and has only one digit (like -1), then num_str[1:] is empty, so the sum over empty is 0.

 35. So we can write:

        if s[0] == '-':
            num_str = s[1:]
            if num_str == '': # but this shouldn't happen because negative numbers have at least one digit
                total = 0
            else:
                total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])
        else:
            total = sum(int(d) for d in s)

 36. However, the problem states that the array contains integers, so negative numbers have at least one digit.

 37. We'll write the code accordingly.

 38. But note: the problem says "Return the complete executable function", so we must write the function as described.

 39. Let's code accordingly.

 40. We'll do:

        def count_nums(arr):
            count = 0
            for num in arr:
                s = str(num)
                if s[0] == '-':
                    # Process negative number
                    num_str = s[1:]
                    # If the number is negative, the first digit (of the absolute value) is negative
                    # and the rest are positive.
                    # If the number has only one digit (like -1), then num_str[1:] is empty.
                    total = -int(num_str[0])
                    # Add the rest of the digits
                    for i in range(1, len(num_str)):
                        total += int(num_str[i])
                    if total > 0:
                        count += 1
                else:
                    total = 0
                    for char in s:
                        total += int(char)
                    if total > 0:
                        count += 1
            return count

 41. However, we can make it more concise by using the sum function for the positive case and for the negative case we can do:

        total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])

 42. But note: if num_str has length 1, then num_str[1:] is empty and sum([])=0, so that's safe.

 43. So we can write:

        if s[0] == '-':
            num_str = s[1:]
            total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])
        else:
            total = sum(int(d) for d in s)

        if total > 0:
            count += 1

 44. However, note: the problem says "sum of digits > 0", so we are checking total>0.

 45. But note: the problem does not require to handle non-integer inputs, so we assume integers.

 46. Let's write the concise version.

 47. We'll do:

        count = 0
        for num in arr:
            s = str(num)
            if s[0] == '-':
                num_str = s[1:]
                # If the number is negative, the first digit (of the absolute value) is negative, the rest positive.
                total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])
            else:
                total = sum(int(d) for d in s)
            if total > 0:
                count += 1
        return count

 48. Test with the examples:

      Example: [-1] -> 
          s = "-1", num_str = "1", total = -1 + sum([]) = -1 -> not counted.

      Example: [11] -> 
          s = "11", total = 1+1 = 2 -> counted.

      Example: [-11] -> 
          s = "-11", num_str = "11", total = -1 + 1 = 0 -> not counted.

      Example: [1, 1, 2] -> 
          1: 1 -> counted
          1: 1 -> counted
          2: 2 -> counted -> total 3.

 49. This matches.

 50. Now, note: the problem says "Return the complete executable function", so we write the function as below.

 51. We don't need any imports because we are using built-in functions.

 52. Write the function.

 53. One more edge: what if the array has a number like -0? But in integers, -0 is the same as 0. 
        In Python, str(-0) is "0", so it would be handled as positive zero -> total=0 -> not counted.

 54. So we are safe.

 Let's write the code.
</think>

def count_nums(arr):
    count = 0
    for num in arr:
        s = str(num)
        if s[0] == '-':
            num_str = s[1:]
            total = -int(num_str[0]) + sum(int(d) for d in num_str[1:])
        else:
            total = sum(int(d) for d in s)
        if total > 0:
            count += 1
    return count

def check(candidate):

    # Check some simple cases
    assert candidate([]) == 0
    assert candidate([-1, -2, 0]) == 0
    assert candidate([1, 1, 2, -2, 3, 4, 5]) == 6
    assert candidate([1, 6, 9, -6, 0, 1, 5]) == 5
    assert candidate([1, 100, 98, -7, 1, -1]) == 4
    assert candidate([12, 23, 34, -45, -56, 0]) == 5
    assert candidate([-0, 1**0]) == 1
    assert candidate([1]) == 1

    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"


check(count_nums)

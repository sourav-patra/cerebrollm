Okay, let's see. I need to implement the fizz_buzz function as described. The problem says: return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13.

Wait, so for all numbers less than n, check if they are divisible by 11 or 13. Then, for each such number, count how many times the digit 7 appears in it. Sum all those counts and return the total.

Let me break it down. For example, if n is 50, then numbers less than 50 divisible by 11 or 13. Let's see: 11, 22, 33, 44 (divisible by 11), and 13, 26, 39 (divisible by 13). Now check each of these numbers for the digit 7. None of them have a 7, so the count is 0. That matches the first example.

Another example: n=78. So numbers less than 78 divisible by 11 or 13. Let's list them. Divisible by 11: 11,22,33,44,55,66,77. Divisible by 13:13,26,39,52,65,78 (but 78 is not less than 78, so up to 65). Now check each for digit 7.

Looking at 77: it has two 7s. So that's 2. Any others? Let's see. 13: no. 26: no. 39: no. 52: no. 65: no. For 11s: 11,22,33,44,55,66: none have 7. So total is 2. Which matches the second example.

Third example: n=79. So numbers less than 79. So 77 is included (since 77 <79), and 78 is excluded. Wait, 78 is divisible by 13 (13*6=78), but 78 is not less than 79, so it's included? Wait, 78 is less than 79, so yes. Wait, 78 is less than 79, so 78 is included. Wait, but 78 is divisible by 13. So 78 is a number to check. Does 78 have a 7? Yes, the first digit is 7. So 78 has one 7. So previous count for n=78 was 2 (from 77), but for n=79, we have 77 (two 7s) and 78 (one 7), so total 3. Which matches the third example.

So the function needs to:

- Iterate through all numbers from 1 to n-1.

- For each number, check if it's divisible by 11 or 13.

- If yes, count the number of '7's in its string representation.

- Sum all those counts.

So the steps are:

1. Initialize a counter to 0.

2. Loop through i from 1 to n-1.

3. If i % 11 == 0 or i %13 ==0:

   a. Convert i to string.

   b. Count how many '7's are in that string.

   c. Add that count to the counter.

4. Return the counter.

Wait, but need to check for divisibility by 11 OR 13. So if either condition is true.

Now, let's test with the examples.

For n=50: numbers up to 49. Divisible by 11: 11,22,33,44. Divisible by 13:13,26,39. None have 7s. So count is 0.

For n=78: numbers up to 77. Divisible by 11: 11,22,33,44,55,66,77. Divisible by 13:13,26,39,52,65. 77 has two 7s. So count is 2.

For n=79: numbers up to 78. So 78 is included. 78 is divisible by 13 (13*6=78). 78 has a '7' in the tens place. So count for 78 is 1. So total is 2 (from 77) +1 (from 78) =3.

So the code should handle that.

Now, code-wise, need to loop from 1 to n-1. For each number, check divisibility.

Wait, but what about numbers that are divisible by both 11 and 13? Like 143 (11*13=143). But for numbers less than n, if n is, say, 150, then 143 would be included. But since it's divisible by both, it's still counted once. So the OR condition is correct.

So the code should check if (i %11 ==0) or (i%13 ==0).

Now, code implementation.

So, in Python:

def fizz_buzz(n: int):
    count = 0
    for i in range(1, n):
        if i % 11 == 0 or i % 13 == 0:
            # count the number of '7's in str(i)
            count += str(i).count('7')
    return count

Wait, let's test this with the examples.

For n=50: loop from 1 to 49. Check each number. For example, 11: 11%11 is 0, so check. str(11) is '11', count of '7' is 0. Similarly for others. So total count 0. Correct.

For n=78: loop up to 77. 77 is included. str(77) has two '7's. So count +=2. So returns 2. Correct.

For n=79: loop up to 78. 78 is included. str(78) has '7' once. So 2 (from 77) +1 (from 78) =3. Correct.

Another test case: n=77. Then numbers less than 77. So 77 is not included. So the count would be 0 (since 77 is excluded). Wait, but 77 is 77, which is less than 77? No, 77 is not less than 77. So for n=77, the loop goes up to 76. So 77 is not included. So the count would be 0. Let's see.

But according to the problem statement, the examples are correct.

So the code seems correct.

Wait, but let's check for n=77. The function would return 0. Let's see.

Another example: n=78, returns 2. n=79 returns 3.

So the code should be correct.

Now, check if there are any edge cases. For example, n=1: loop from 1 to 0, which is empty. So returns 0. Correct.

n=11: numbers less than 11. So 1-10. Divisible by 11: none (since 11 is not less than 11). Divisible by 13: none. So returns 0.

Another example: n=13. Numbers less than 13. Divisible by 11: 11. Divisible by 13: none. So check 11. '11' has no 7s. So returns 0.

n=14: numbers up to 13. 13 is included. 13 is divisible by 13. str(13) has no 7s. So count 0.

n=77: as before, returns 0.

n=78: returns 2.

So the code seems to handle all cases.

Now, check if the code is correctly written.

Yes, the code loops from 1 to n-1, checks divisibility, counts the 7s in the string.

So the function should be correct.

Now, the problem says to return the complete executable function with any needed imports. But in this case, no imports are needed. So the code is as written.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should be:

def fizz_buzz(n: int):
    count = 0
    for i in range(1, n):
        if i % 11 == 0 or i % 13 == 0:
            count += str(i).count('7')
    return count

Yes, that's it. Let me check if there's any possible mistake.

Wait, for example, if a number has multiple 7s, like 777, it would count all three. Which is correct.

Another example: n=80. Then numbers up to 79. So 77 (two 7s), 78 (one 7), and 77 is included. So total 3. Wait, 77 is less than 80, yes. So for n=80, the count would be 2 (from 77) +1 (from 78) =3. Wait, but 78 is less than 80, yes. So yes.

So the code should handle that.

Thus, the code is correct.
</think>

def fizz_buzz(n: int):
    count = 0
    for i in range(1, n):
        if i % 11 == 0 or i % 13 == 0:
            count += str(i).count('7')
    return count



METADATA = {}


def check(candidate):
    assert candidate(50) == 0
    assert candidate(78) == 2
    assert candidate(79) == 3
    assert candidate(100) == 3
    assert candidate(200) == 6
    assert candidate(4000) == 192
    assert candidate(10000) == 639
    assert candidate(100000) == 8026


check(fizz_buzz)

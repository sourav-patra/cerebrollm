Okay, let's see. I need to implement the fib4 function without using recursion. The problem says it's similar to Fibonacci but with a different recurrence relation. Let me check the definitions again.

The base cases are:
fib4(0) = 0
fib4(1) = 0
fib4(2) = 2
fib4(3) = 0

For n >=4, fib4(n) = fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4).

So, for example, fib4(4) would be fib4(3) + fib4(2) + fib4(1) + fib4(0) = 0 + 2 + 0 + 0 = 2. Wait, but the examples given are for n=5,6,7. Let's check the examples.

The example says fib4(5) is 4. Let's compute that.

Compute fib4(4) first. As above, 0+2+0+0=2.

Then fib4(5) = fib4(4) + fib4(3) + fib4(2) + fib4(1) = 2 + 0 + 2 + 0 = 4. Which matches the example. Good.

fib4(6) should be fib4(5) + fib4(4) + fib4(3) + fib4(2) = 4 + 2 + 0 + 2 = 8. Which matches the example. So that's correct.

So the problem is to compute this efficiently without recursion. So recursion would be bad for large n because it's exponential. So we need to use iterative approach, probably with a loop and keeping track of the last four values.

Since for each n >=4, we need the previous four terms. So for n=4, we need terms 0-3. So the idea is to start from the base cases and build up to n.

So for n less than 4, return the base case. For n >=4, compute iteratively.

Let's outline the steps.

If n is 0, return 0.

n=1, 0.

n=2, 2.

n=3, 0.

For n >=4, we can start from 4 up to n, keeping track of the last four values.

So, for example, let's say we have variables a, b, c, d representing fib4(n-4), fib4(n-3), fib4(n-2), fib4(n-1). Wait, maybe better to have a list or variables that hold the last four values.

Let's think: for n=4, the previous four terms are n-1=3 (0), n-2=2 (2), n-3=1 (0), n-4=0 (0). So sum is 0+2+0+0=2.

So for each step, we can keep a list of the last four values. Let's say we have a list that starts with [0, 0, 2, 0] for n=0,1,2,3.

Then for n=4, the next value is sum of the list. Then we shift the list: remove the first element, add the new value.

Wait, but for n=4, the list would be [0,0,2,0], sum is 2. Then for n=5, the list becomes [0,2,0,2], sum is 0+2+0+2=4. Which matches the example.

Yes, so the approach is to maintain a list of the last four values. For n <4, return the base case. For n >=4, iterate from 4 up to n, updating the list each time.

So the code would be:

If n is 0,1,2,3, return the corresponding value.

Else, initialize a list with the base cases [0,0,2,0].

Then for i in range(4, n+1):

   next_val = sum(current_list)

   current_list = current_list[1:] + [next_val]

Wait, but for n=4, the current_list is [0,0,2,0], sum is 2. Then current_list becomes [0,2,0,2].

Then for n=5, sum is 0+2+0+2=4. So yes.

So the code can be written as:

def fib4(n):
    if n == 0 or n == 1:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0
    else:
        # Initialize the list with the base cases for n=0,1,2,3
        fibs = [0, 0, 2, 0]
        for i in range(4, n+1):
            next_val = sum(fibs)
            fibs = fibs[1:] + [next_val]
        return fibs[-1]

Wait, let's test this with n=4. The loop runs for i=4 (since range(4,5) is just 4). So next_val is sum([0,0,2,0]) = 2. Then fibs becomes [0,2,0,2]. Then return fibs[-1], which is 2. Which is correct for n=4.

For n=5, the loop runs for i=4 and i=5. Wait, no. Wait, for n=5, the loop runs from 4 to 5 (inclusive). So for i=4, compute 4th term (n=4), then for i=5, compute 5th term.

Wait, the loop is for i in range(4, n+1). So for n=5, the loop runs for i=4 and i=5. Wait, no: range(4,6) is 4,5. So for n=5, the loop runs twice. Wait, but for n=5, the code should compute up to 5.

Wait, let's see. Let's take n=5.

Initially, fibs is [0,0,2,0].

First iteration (i=4): next_val = sum(fibs) = 0+0+2+0=2. fibs becomes [0,2,0,2].

Second iteration (i=5): next_val = sum([0,2,0,2]) = 4. fibs becomes [2,0,2,4]. Then return 4. Which is correct.

Yes, so for n=5, the code returns 4. Which matches the example.

Similarly, for n=6, the loop runs for i=4,5,6.

After i=4: [0,2,0,2]

i=5: [2,0,2,4]

i=6: sum is 2+0+2+4=8. So fibs becomes [0,2,4,8], and returns 8. Which matches the example.

So this approach works.

Now, check for n=2. The code returns 2, which is correct.

So the code should handle all cases.

Now, let's code this.

But need to handle the base cases first.

So the code:

def fib4(n):
    if n < 2:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0
    else:
        fibs = [0, 0, 2, 0]
        for _ in range(4, n+1):
            next_val = sum(fibs)
            fibs = fibs[1:] + [next_val]
        return fibs[-1]

Wait, but for n=4, the loop runs once (since range(4,5) is one iteration). So for n=4, the code returns the next_val after the first iteration, which is 2. Correct.

Testing with the examples:

fib4(5) should return 4. Let's see:

n=5, so the loop runs for i=4 and i=5 (since range(4,6) is 4,5). Wait, no: range(4, n+1) when n=5 is range(4,6), which is 4 and 5. So two iterations.

Wait, for n=5, the code will compute up to i=5, which is the 5th term. So yes.

Another way: for n=4, the loop runs once (i=4), which computes the 4th term.

So the code seems correct.

Now, check edge cases. For example, n=0, returns 0. n=1, 0. n=2, 2. n=3, 0. All correct.

Another test: n=4, returns 2. Let's compute manually:

fib4(4) = fib4(3)+fib4(2)+fib4(1)+fib4(0) = 0+2+0+0=2. Correct.

So the code should be correct.

Now, check if the code is efficient. Since it's O(n) time and O(1) space (since the list is fixed size 4), it's efficient.

So the code should be as written.

Wait, but in Python, the list slicing and creating new lists might be O(1) since the list is fixed size. So the space is O(1), which is good.

So the code should be correct.

Now, write the code as per the problem's instruction. The problem says to return the complete executable function with any needed imports. But in this case, no imports are needed. So the code is as above.

Wait, but let's check the example for n=7. The example says fib4(7) is 14.

Let's compute step by step.

n=0:0

n=1:0

n=2:2

n=3:0

n=4: sum(0,0,2,0)=2

n=5: sum(0,2,0,2)=4

n=6: sum(2,0,2,4)=8

n=7: sum(0,2,4,8)=14. Yes, which matches the example.

So for n=7, the code would compute up to i=7.

So the code should return 14 for n=7.

Thus, the code is correct.

So the final code is as written.
</think>

def fib4(n: int):
    if n < 2:
        return 0
    elif n == 2:
        return 2
    elif n == 3:
        return 0
    else:
        fibs = [0, 0, 2, 0]
        for _ in range(4, n + 1):
            next_val = sum(fibs)
            fibs = fibs[1:] + [next_val]
        return fibs[-1]



METADATA = {}


def check(candidate):
    assert candidate(5) == 4
    assert candidate(8) == 28
    assert candidate(10) == 104
    assert candidate(12) == 386


check(fib4)

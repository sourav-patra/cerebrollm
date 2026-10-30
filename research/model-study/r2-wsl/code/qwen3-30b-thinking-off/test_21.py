Okay, I need to implement the greatest common divisor function in Python. Let me think about how to do this. The problem says to return the GCD of two integers a and b. I remember that the Euclidean algorithm is the standard way to compute GCD efficiently.

So the Euclidean algorithm works by repeatedly applying the division remainder. The basic idea is that the GCD of two numbers also divides their difference. So, for example, GCD(a, b) = GCD(b, a mod b), and we keep doing this until one of the numbers becomes zero. Then the other number is the GCD.

Let me recall the steps. Let's say we have a and b. If b is zero, then the GCD is a. Otherwise, we compute GCD(b, a mod b). This is a recursive approach, but since the problem doesn't specify recursion or iteration, I can use either. However, for efficiency, especially with large numbers, the iterative method might be better to avoid stack overflow.

Wait, but in Python, recursion depth might be a problem for very large numbers, but for the purpose of this problem, maybe recursion is acceptable. But the Euclidean algorithm is usually implemented iteratively. Let me check.

For example, take the example given: greatest_common_divisor(25, 15). Let's walk through it. 25 divided by 15 is 1 with remainder 10. Then GCD(15, 10). 15 divided by 10 is 1 with remainder 5. Then GCD(10,5). 10 divided by 5 is 2 with remainder 0. So GCD is 5. That matches the example.

So the iterative approach would be:

while b != 0:
    a, b = b, a % b
return a

Wait, but I need to make sure that a and b are handled correctly. Let's see. Let's say a is 3 and b is 5. Then in the first step, a=3, b=5. Then we swap them because b is not zero. Wait, no. Wait, the algorithm is: while b is not zero, set a to b, and b to a mod b. Wait, but in code, it's better to use a temporary variable or swap.

Wait, the standard iterative Euclidean algorithm is:

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

Yes, that's right. So in the loop, as long as b is not zero, we replace a with b and b with the remainder of a divided by b. Once b becomes zero, a is the GCD.

So for the example of 25 and 15:

Initial a=25, b=15.

First iteration: b is 15 (not zero), so a becomes 15, b becomes 25 % 15 = 10.

Second iteration: a=15, b=10. Now b is 10, so a becomes 10, b becomes 15 % 10 =5.

Third iteration: a=10, b=5. b is 5, so a becomes 5, b becomes 10 %5=0.

Now b is 0, loop ends. Return a=5. Correct.

Another example: 3 and 5. a=3, b=5.

First iteration: a=5, b=3%5=3. Wait, no. Wait, a is 3, b is 5. So in the first step, a, b = b, a % b → a=5, b=3%5=3.

Wait, 3 divided by 5 is 0 with remainder 3. So yes, 3%5 is 3.

Then next step: a=5, b=3. Now, a, b = 3, 5%3=2.

Then a=3, b=2. Next: a=2, b=3%2=1.

Then a=2, b=1. Next: a=1, b=2%1=0. Now b is 0, return a=1. Which matches the example.

So the code should handle both cases where a < b and a > b.

So the function can be written as:

def greatest_common_divisor(a: int, b: int) -> int:
    while b != 0:
        a, b = b, a % b
    return a

Wait, but what if a or b is negative? The problem statement says integers, but GCD is usually defined for positive integers. However, the GCD of negative numbers is the same as their absolute values. For example, GCD(-25, 15) is 5. But the problem's examples are positive, so maybe the inputs are positive. But the problem statement says "two integers a and b", so they could be negative. However, the modulus operation in Python for negative numbers might behave differently. Wait, but the Euclidean algorithm typically uses absolute values, but the algorithm as written would handle it because the modulus will eventually make the numbers positive.

Wait, let's test with negative numbers. Let's say a= -25, b=15.

In the first step, a=-25, b=15. Then, while b !=0, we do a, b = b, a % b.

So a becomes 15, b becomes (-25) % 15. What's (-25) % 15 in Python? Let's see. Python's modulus returns a result with the same sign as the divisor. So -25 divided by 15 is -2 with remainder 5, because 15*(-2) = -30, so -25 - (-30) =5. So (-25) %15 is 5. So b becomes 5.

Then next step: a=15, b=5. Then a becomes 5, b=15%5=0. Return 5. Which is correct.

Another example: a=15, b=-25. Let's see. a=15, b=-25. Then in the loop, b is not zero. So a, b = -25, 15 % (-25). Wait, 15 divided by -25 is -1 with remainder 15 - (-25)*(-1) = 15 -25 = -10. Wait, but modulus in Python: 15 % (-25) would be -10, because the remainder has the same sign as the divisor. So 15 = (-25)*(-1) + (-10). So 15 % (-25) is -10. Then b becomes -10.

Then next step: a=-25, b=-10. Now, a, b = -10, (-25) % (-10). Wait, but modulus with negative divisor. Let's compute (-25) % (-10). Well, the modulus should be non-negative if the divisor is positive, but here divisor is negative. Wait, but in Python, the modulus result has the same sign as the divisor. So (-25) % (-10) would be... Let's see. The division is floor division. So -25 // -10 is 2 (since -25 / -10 is 2.5, floor is 2). Then the remainder is -25 - (-10)*2 = -25 +20 = -5. So (-25) % (-10) is -5. So b becomes -5.

Then next step: a=-10, b=-5. Now, a, b = -5, (-10) % (-5). (-10) divided by -5 is 2, remainder 0. So b becomes 0. Return a=-5. But GCD is a positive number. Wait, but the problem says "greatest common divisor", which is always positive. So the function should return the absolute value? Wait, but in the examples given, the inputs are positive, so maybe the problem assumes positive inputs. However, the problem statement says "integers", so perhaps we need to handle negative numbers by taking absolute values.

Wait, but according to the Euclidean algorithm, the GCD is defined as a positive integer. So even if the inputs are negative, the GCD should be positive. So perhaps the code should take absolute values first. But the problem's examples don't have negative numbers, so maybe the test cases only use positive numbers. However, to be safe, perhaps the code should handle negative numbers by converting to positive.

Wait, but in the code I wrote earlier, when a and b are negative, the algorithm might return a negative number. For example, if a= -5 and b=0, then the GCD would be -5, but GCD should be 5. So perhaps the code should return the absolute value of a at the end.

Wait, but in the loop, when b becomes zero, a is the GCD. But if a is negative, then the GCD would be negative. However, GCD is defined as a positive integer. So perhaps the code should return abs(a) at the end.

Wait, let's test with a= -5, b=0. The loop would not run, so return a=-5. But GCD(5,0) is 5. So the code should return the absolute value.

But the problem statement's examples are positive, so maybe the test cases only use positive numbers. However, to make the function robust, perhaps it's better to take absolute values of a and b at the start.

Wait, but the Euclidean algorithm works with absolute values. So perhaps the correct approach is to take the absolute values of a and b before processing.

So modifying the code to:

a = abs(a)
b = abs(b)

But the problem says "two integers a and b", so maybe the inputs can be negative, but the GCD is positive. So the function should return the positive GCD.

So perhaps the correct code should take absolute values first.

Wait, let's see. Let's say a is negative. For example, a=-25, b=15. The GCD is 5. If we take absolute values first, then a=25, b=15, and the algorithm proceeds as before, returning 5.

So to handle negative numbers correctly, the code should take absolute values of a and b before applying the Euclidean algorithm.

But the problem statement's examples don't include negative numbers, but the function's parameters are integers, so it's safer to handle them.

Wait, but the problem says "Return a greatest common divisor of two integers a and b". The GCD is always positive, so the function should return a positive integer.

Therefore, the code should take absolute values of a and b before processing.

So the correct implementation would be:

def greatest_common_divisor(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b != 0:
        a, b = b, a % b
    return a

Wait, but let's test with a=0 and b=0. Wait, GCD(0,0) is undefined, but the problem probably assumes that at least one of a or b is non-zero. However, the problem's examples don't cover that. But according to the problem statement, the inputs are integers, but the examples have positive numbers. So perhaps the test cases won't include both zeros.

But for the purpose of the problem, we can assume that at least one of a or b is non-zero.

So the code with absolute values should handle negative numbers correctly.

Wait, but let's check the example given: greatest_common_divisor(3,5) returns 1. With the code above, abs(3)=3, abs(5)=5. Then the loop proceeds as before, returning 1. Correct.

Another example: 25 and 15. abs(25)=25, abs(15)=15. The loop returns 5. Correct.

So adding the absolute values at the start ensures that the algorithm works for negative inputs as well.

But the problem statement's examples don't have negative numbers, but the function should handle any integers. So including the abs is better.

Wait, but the problem says "Return a greatest common divisor of two integers a and b". The GCD is defined as a positive integer, so the code must return a positive value. Therefore, taking absolute values is necessary.

So the correct code should include abs(a) and abs(b) at the beginning.

Wait, but let's see: if a is 0 and b is 5, then GCD(0,5) is 5. The code would take abs(0)=0, abs(5)=5. Then the loop: while b !=0 (5 !=0), so a becomes 5, b becomes 0%5=0. Then loop ends, return a=5. Correct.

If a is 5 and b is 0, then the loop doesn't run, return 5. Correct.

So the code with abs is correct.

Therefore, the function should first take the absolute values of a and b.

So the code would be:

def greatest_common_divisor(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a

Wait, in Python, while b: is equivalent to while b != 0:.

Yes, because in Python, 0 is False, and non-zero is True.

So this code should work.

Let me check the edge cases.

Case 1: a=0, b=0. But GCD(0,0) is undefined. However, the problem probably doesn't test this case. The code would return 0, but that's not correct. But since the problem's examples don't include this, and the problem statement says "two integers", perhaps we can assume that at least one is non-zero.

Case 2: a=0, b=5. Returns 5. Correct.

Case 3: a=5, b=0. Returns 5. Correct.

Case 4: a=-5, b=15. abs(a)=5, abs(b)=15. Then the loop: a=15, b=5%15=5. Then a=5, b=15%5=0. Return 5. Correct.

So the code handles negative numbers correctly.

Therefore, the correct implementation is to take absolute values first, then apply the Euclidean algorithm.

So the function should be written as such.

Now, the problem says to return the complete executable function with any needed imports. But the Euclidean algorithm doesn't require any imports. So the code will have no imports.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should be:

def greatest_common_divisor(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a

Wait, but let's check if the problem's examples are covered.

For (3,5): abs(3)=3, abs(5)=5. Then loop:

b=5 !=0 → a=5, b=3%5=3.

b=3 !=0 → a=3, b=5%3=2.

b=2 !=0 → a=2, b=3%2=1.

b=1 !=0 → a=1, b=2%1=0.

Loop ends, return 1. Correct.

Another example: (25,15). abs(25)=25, abs(15)=15.

Loop:

b=15 → a=15, b=25%15=10.

b=10 → a=10, b=15%10=5.

b=5 → a=5, b=10%5=0.

Return 5. Correct.

So the code works.

Therefore, the correct function is as written.
</think>

def greatest_common_divisor(a: int, b: int) -> int:
    a = abs(a)
    b = abs(b)
    while b:
        a, b = b, a % b
    return a



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate(3, 7) == 1
    assert candidate(10, 15) == 5
    assert candidate(49, 14) == 7
    assert candidate(144, 60) == 12

check(greatest_common_divisor)

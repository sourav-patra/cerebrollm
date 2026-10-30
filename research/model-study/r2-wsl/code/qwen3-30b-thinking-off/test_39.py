Okay, let's see. I need to implement a function that sorts numbers given as words in a string. The input is a space-separated string of number words from 'zero' to 'nine', and I have to return them sorted from smallest to largest.

First, I should figure out how to map each word to its numerical value. Like, 'zero' is 0, 'one' is 1, up to 'nine' being 9. So I need a dictionary that maps each word to its integer value.

Wait, the function takes a string like 'three one five' and returns 'one three five'. So the steps are: split the input string into a list of words, convert each word to its corresponding number, sort the numbers, then convert them back to words in order.

Right. So first, split the input string into individual words. Then, for each word, get its numerical value. Sort those values, then map back to the words.

So I need a mapping from the word to the number. Let's create a dictionary for that. Let's see:

zero: 0, one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8, nine:9.

So the dictionary would be:

num_map = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9
}

Then, for the input string, split into words. For each word, get the number from num_map. Then sort the list of numbers. Then, for each number in the sorted list, find the corresponding word. Wait, but how to reverse the mapping? Because the numbers are 0-9, but the words are unique. So I can create a reverse mapping from number to word.

Wait, but the numbers are from 0 to 9, so I can create a list where index 0 is 'zero', index 1 is 'one', etc. Or create a reverse dictionary.

Alternatively, after sorting the numbers, I can use the reverse mapping. Let's see.

So, for example, if the input is 'three one five', split into ['three', 'one', 'five']. Convert to [3,1,5]. Sort to [1,3,5]. Then convert back to ['one', 'three', 'five'], join into 'one three five'.

So the key is to have a way to convert the number back to the word. So perhaps create a list where the index corresponds to the number. Like:

words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

Then, for a number n, the word is words[n].

Wait, but the numbers are 0-9, so that's a list of 10 elements. So for example, 0 is words[0], 1 is words[1], etc.

So the plan is:

1. Split the input string into a list of words.
2. For each word, get its numerical value using the num_map (which maps word to number).
3. Sort the list of numbers.
4. Convert each number back to the word using the words list.
5. Join the words back into a string with spaces.

Wait, but the num_map is from word to number. So for each word in the input, we get the number. Then sort those numbers. Then for each number in the sorted list, get the corresponding word from the words list.

Yes. So the words list is ordered from zero to nine.

So let's code that.

First, define the words list. Wait, but the problem says the valid choices are from 'zero' to 'nine', so the words list should be exactly those.

So:

words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

But wait, the words list is ordered by the numerical value. So index 0 is 'zero', index 1 is 'one', etc.

So for a number n, the word is words[n].

So the steps:

- Split the input string into words.
- For each word, find its index in the words list? Wait, no. Wait, the num_map is a dictionary that maps the word to the index (the number). So for example, 'three' maps to 3.

Wait, the num_map would be:

num_map = {word: index for index, word in enumerate(words)}

But since the words list is ordered, this would work.

Alternatively, create the num_map as a dictionary with the words as keys and their numerical values as values.

So, for example:

num_map = {
    'zero': 0,
    'one': 1,
    ...
}

But to avoid writing all that, perhaps generate it from the words list.

But since the problem is small, maybe it's easier to just define it directly.

But in code, perhaps better to generate it.

Wait, but for the code, I can create the words list and then create the num_map from it.

Wait, but the function needs to be self-contained. So perhaps:

words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

num_map = {word: i for i, word in enumerate(words)}

Then, for each word in the input, get the number from num_map.

Wait, but the input words are exactly the ones in the words list, so this should work.

So the steps in code:

def sort_numbers(numbers: str) -> str:
    words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    num_map = {word: idx for idx, word in enumerate(words)}
    # Split the input string into a list of words
    word_list = numbers.split()
    # Convert each word to its numerical value
    numbers_list = [num_map[word] for word in word_list]
    # Sort the numbers
    numbers_list.sort()
    # Convert back to words using the words list
    sorted_words = [words[num] for num in numbers_list]
    # Join them into a string
    return ' '.join(sorted_words)

Wait, but let's test this with the example.

Input: 'three one five'

Split into ['three', 'one', 'five']

num_map['three'] is 3, 'one' is 1, 'five' is 5.

numbers_list is [3,1,5], sorted becomes [1,3,5].

sorted_words: words[1] is 'one', words[3] is 'three', words[5] is 'five'.

So the output is 'one three five', which matches the example.

Looks good.

Now, check if all possible inputs are covered. The problem states that the input is a space-delimited string of numberals from 'zero' to 'nine', so all words are valid.

So the code should work.

Now, check for possible errors. For example, if the input has a word not in the list, but the problem says valid choices are those, so we don't need to handle that.

So the code should be correct.

Now, write the code as per the instructions. The function needs to be complete with any needed imports. Wait, the code uses no imports, since it's just using standard lists and dictionaries.

Wait, the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should have the function, and any necessary imports. But in this case, no imports are needed. So the code is as written.

Wait, but the words list is defined inside the function. So each time the function is called, it creates the words list and num_map. That's acceptable, since it's a small list.

Alternatively, define them outside, but since it's a function, it's better to define them inside to avoid global variables.

So the code as written should be correct.

Let me check for possible typos.

Wait, the words list is correctly ordered from zero to nine.

Yes: 'zero' (0), 'one' (1), ..., 'nine' (9).

Yes.

So the code should work.

Another test case: input 'nine eight seven' should return 'seven eight nine'.

Let's see:

split into ['nine', 'eight', 'seven'].

num_map: 'nine' is 9, 'eight' is 8, 'seven' is 7.

numbers_list: [9,8,7] → sorted [7,8,9].

sorted_words: words[7] is 'seven', words[8] is 'eight', words[9] is 'nine'.

So output 'seven eight nine', which is correct.

Another test: input 'zero' → 'zero'.

Yes.

So the code should be correct.

Now, write the code as per the instructions.

The function is named sort_numbers, takes a string, returns a string.

So the code block should be:

from typing import List

def sort_numbers(numbers: str) -> str:
    words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    num_map = {word: idx for idx, word in enumerate(words)}
    word_list = numbers.split()
    numbers_list = [num_map[word] for word in word_list]
    numbers_list.sort()
    sorted_words = [words[num] for num in numbers_list]
    return ' '.join(sorted_words)

Wait, but the problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

So the code should include the import for List, but since the function uses List in the type hint, but the problem says to include any needed imports. Wait, the function signature has 'List' in it, so we need to import List from typing.

Wait, the problem's example code includes:

from typing import List

So the code should have that import.

So the code as written includes that.

Yes.

So the code is correct.

Wait, but in the code I wrote, the words list is defined inside the function. That's okay.

So the final code should be as above.

Let me check if there's any possible mistake.

Wait, the problem says "space-delimited string of numberals from 'zero' to 'nine'". So the input words are all valid, so no need to check for invalid words.

Yes.

So the code should work.

Another possible edge case: input is empty string. But the problem says the input is a space-delimited string of those words, so probably the input has at least one word. But the code would handle empty string by splitting into empty list, sorting empty list, etc. But since the problem states valid inputs, we don't need to handle that.

So the code is correct.
</think>

from typing import List


def sort_numbers(numbers: str) -> str:
    words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    num_map = {word: idx for idx, word in enumerate(words)}
    word_list = numbers.split()
    numbers_list = [num_map[word] for word in word_list]
    numbers_list.sort()
    sorted_words = [words[num] for num in numbers_list]
    return ' '.join(sorted_words)



METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('') == ''
    assert candidate('three') == 'three'
    assert candidate('three five nine') == 'three five nine'
    assert candidate('five zero four seven nine eight') == 'zero four five seven eight nine'
    assert candidate('six five four three two one zero') == 'zero one two three four five six'

check(sort_numbers)

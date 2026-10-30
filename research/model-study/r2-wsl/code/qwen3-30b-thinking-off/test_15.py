We are going to implement the function as described.
 Steps:
 1. If the string contains whitespace, split on whitespace (using split() which by default splits on whitespace and removes any empty strings).
 2. If there is no whitespace, then check for commas. If there are commas, split on commas.
 3. If there are neither whitespace nor commas, then count the number of lower-case letters that have an odd order in the alphabet (where 'a' is 0, 'b' is 1, ... 'z' is 25).
    Note: We only count lower-case letters. We ignore non-alphabet characters.

 However, note the examples:
   split_words("abcdef") == 3 
   Why? 
        a:0 (even), b:1 (odd), c:2 (even), d:3 (odd), e:4 (even), f:5 (odd) -> so odd counts: b, d, f -> 3.

 Implementation:
   We'll check for whitespace first: if there's any space, tab, newline, etc. (i.e., if the string has any whitespace) then split by whitespace.
   But note: the example "Hello world!" has a space, so we split into ["Hello", "world!"].

   However, note that the example "Hello,world!" has a comma but no space? Actually, the example says split on commas if no whitespace. So we check for whitespace first.

   So:
     if there is any whitespace in the string -> split by whitespace (using str.split() which splits on any whitespace and returns non-empty parts).
     else if there is a comma -> split by commas.
     else -> count the lower-case letters that have an odd index (where 'a' is 0, so odd indices: 1,3,5,...).

 Important: We are only counting lower-case letters. We ignore uppercase and non-alphabet.

 Let's break down:

   Step 1: Check for whitespace. We can check if any character in the string is a whitespace (using str.isspace() for the whole string? but note: we don't want to split if there's no whitespace at all). Actually, we can check: if the string has any whitespace, then split by whitespace.

   However, note: the problem says "split on whitespace", meaning we split at every whitespace. We can use the built-in split() which does that.

   But note: the example "Hello world!" has a space, so we split into two parts.

   Step 2: If there's no whitespace, then check for commas. We can check if ',' is in the string? But note: the problem says "if no commas exists", meaning if there are no commas then we do the count.

   However, note: the problem says "if no whitespaces exists in the text you should split on commas", so we check for whitespace first, then if no whitespace, check for commas.

   Step 3: If there are no commas either, then we do the count.

   But note: what if the string has both? We split on whitespace first, so we don't get to the comma splitting.

   So algorithm:

     if ' ' in txt or '\t' in txt or '\n' in txt ...? Actually, we can use: if txt contains any whitespace character.

     However, a simpler way: use the fact that str.split() without arguments splits on any whitespace and returns a list. But note: we don't want to split if there's no whitespace? Actually, we can check: if the string has any whitespace, then we split by whitespace (using split() which handles multiple whitespace and returns non-empty tokens). But note: the problem says "split on whitespace", meaning we split at every whitespace.

     Alternatively, we can do:

        if any(c.isspace() for c in txt):
            return txt.split()

        elif ',' in txt:
            return txt.split(',')

        else:
            # Count the lower-case letters that have an odd order (i.e., ord(c) - ord('a') is odd)
            count = 0
            for c in txt:
                if c.islower() and c.isalpha():
                    # Calculate the index: ord(c) - ord('a')
                    index = ord(c) - ord('a')
                    if index % 2 == 1:
                        count += 1
            return count

   However, note: the problem says "return the number", so in the else case we return an integer.

   But wait: the example "abcdef" returns 3, which is an integer.

   But note: the problem says "split_words("abcdef") == 3", so we return 3.

   However, the problem also says: "if no commas exists you should return the number ...", so we return the integer.

   But note: the examples return a list in the first two cases and an integer in the third.

   So the function returns either a list or an integer.

   Let's test with the examples:

     Example 1: "Hello world!" -> has space -> split() -> ['Hello', 'world!'] -> matches.

     Example 2: "Hello,world!" -> no space? Actually, it has a comma but no space? So we check: does it have whitespace? It doesn't have a space, so we check for commas -> yes, so split by commas -> ['Hello', 'world!'] -> matches.

     Example 3: "abcdef" -> no whitespace, no comma -> so we count: 
          a:0 -> even -> skip
          b:1 -> odd -> count=1
          c:2 -> even -> skip
          d:3 -> odd -> count=2
          e:4 -> even -> skip
          f:5 -> odd -> count=3 -> returns 3.

   However, note: the example says "abcdef" (all lower-case) so we count all.

   But what about non-alphabet? For example, if the string is "a1b", then we only count 'a' and 'b'. 
        'a':0 -> even -> skip
        '1': not a letter -> skip
        'b':1 -> odd -> count=1.

   So we must check for isalpha and islower.

   Let's code accordingly.

   Important: We must not count uppercase. The problem says "lower-case letters".

   We'll write the function accordingly.

   However, note: the problem says "ord('a') = 0", so we are using the standard ASCII.

   We'll assume the input is ASCII.

   Let's write the code.

   But note: the problem says "if no whitespaces exists in the text", meaning if there is no whitespace at all. Similarly for commas.

   We can check for whitespace by: if there's any whitespace character (space, tab, newline, etc.) then we split by whitespace.

   We can use: 
        if any(c.isspace() for c in txt):

   However, note: the string might be empty? The problem doesn't specify, but we'll assume non-empty? But to be safe, we can handle empty string.

   For empty string:
        It has no whitespace? Actually, an empty string has no whitespace -> then check for commas: no commas -> then we count: no lower-case letters -> returns 0.

   But the problem doesn't specify empty string, so we'll assume the input is as per examples.

   Let's code accordingly.

   We'll do:

        if any(c.isspace() for c in txt):
            return txt.split()
        elif ',' in txt:
            return txt.split(',')
        else:
            count = 0
            for c in txt:
                if c.islower() and c.isalpha():
                    if (ord(c) - ord('a')) % 2 == 1:
                        count += 1
            return count

   However, note: the problem says "split on commas", meaning we split at every comma. The split(',') method does that.

   But note: what if there are multiple commas? For example, "a,b,c" -> split by commas gives ['a','b','c'].

   This matches the requirement.

   Let's test with a string that has both space and comma? 
        Example: "Hello, world" -> has space? Yes, so we split by whitespace: ['Hello,', 'world'] -> but note: the comma is attached to "Hello,". 
        However, the example "Hello,world!" was split by comma because there was no space? Actually, in "Hello,world!" there is no space, so we split by comma.

        But in "Hello, world", there is a space, so we split by space: so we get ['Hello,', 'world'].

        This is acceptable.

   Now, note: the problem says "split on whitespace" meaning we split at every whitespace, so the comma is not removed by the whitespace split.

   So the example "Hello, world" becomes ['Hello,', 'world'].

   This is as per the problem.

   We'll write the function accordingly.

   However, note: the problem says "if no whitespaces exists", meaning if there is no whitespace at all, then we split on commas. So if there is a space, we don't look at commas.

   So the above condition is correct.

   Let's write the code.

   We don't need any imports for this.

   But note: the problem says "Return the complete executable function with any needed imports, in one Python code block"

   We don't need any imports.

   So the function is:

        def split_words(txt):
            if any(c.isspace() for c in txt):
                return txt.split()
            elif ',' in txt:
                return txt.split(',')
            else:
                count = 0
                for c in txt:
                    if c.islower() and c.isalpha():
                        if (ord(c) - ord('a')) % 2 == 1:
                            count += 1
                return count

   However, note: the problem says "ord('a') = 0", so we are using (ord(c) - ord('a')) to get the index.

   But note: the problem says "odd order", meaning the index (starting at 0 for 'a') is odd? 
        Actually, the problem says: "ord('a') = 0, ord('b') = 1, ...", so the order is the index. 
        We want the index to be odd: so index % 2 == 1.

   This matches.

   Let's test with a small example: 
        'b': index = 1 -> odd -> count.
        'a': index=0 -> even -> skip.

   So the code is correct.

   But note: the problem says "lower-case letters", so we are checking with islower() and isalpha().

   We'll write the function as above.

   However, note: the problem says "if no commas exists", meaning if there are no commas at all. So we check for the presence of a comma. We are using `',' in txt` which is efficient.

   We'll write the function.

   One more edge: what if the string has a comma but also has whitespace? Then we split by whitespace (because we check for whitespace first) and ignore the comma.

   This is as per the problem.

   Now, let's write the code in the required format.

   Note: The problem says "Return the complete executable function with any needed imports, in one Python code block, without explanations."

   So we output:

        def split_words(txt):
            if any(c.isspace() for c in txt):
                return txt.split()
            elif ',' in txt:
                return txt.split(',')
            else:
                count = 0
                for c in txt:
                    if c.islower() and c.isalpha():
                        if (ord(c) - ord('a')) % 2 == 1:
                            count += 1
                return count

   However, note: the problem says "split on whitespace", and the built-in split() without arguments does exactly that.

   But note: the problem says "split on whitespace", and the example "Hello world!" becomes ["Hello", "world!"].

   The built-in split() for "Hello world!" returns ['Hello', 'world!'].

   So it's correct.

   Let's run through the examples:

        Example 1: "Hello world!" -> has space -> split() -> ['Hello', 'world!'] -> correct.

        Example 2: "Hello,world!" -> no space? Actually, it has a comma but no space? So we check: does it have whitespace? It doesn't have a space, so we check for comma: yes -> split by comma -> ['Hello', 'world!'] -> correct.

        Example 3: "abcdef" -> no space, no comma -> count: 
            a:0 -> even -> skip
            b:1 -> odd -> count=1
            c:2 -> even -> skip
            d:3 -> odd -> count=2
            e:4 -> even -> skip
            f:5 -> odd -> count=3 -> returns 3.

   So it matches.

   We'll write the function.

   Note: We are not using any imports, so no need for import statements.

   Final code:
</think>

def split_words(txt):
    if any(c.isspace() for c in txt):
        return txt.split()
    elif ',' in txt:
        return txt.split(',')
    else:
        count = 0
        for c in txt:
            if c.islower() and c.isalpha():
                if (ord(c) - ord('a')) % 2 == 1:
                    count += 1
        return count

def check(candidate):

    assert candidate("Hello world!") == ["Hello","world!"]
    assert candidate("Hello,world!") == ["Hello","world!"]
    assert candidate("Hello world,!") == ["Hello","world,!"]
    assert candidate("Hello,Hello,world !") == ["Hello,Hello,world","!"]
    assert candidate("abcdef") == 3
    assert candidate("aaabb") == 2
    assert candidate("aaaBb") == 1
    assert candidate("") == 0

check(split_words)

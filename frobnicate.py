#!/usr/bin/env python3
# davep 20241019 ; replace alphabetical non-keyword strings with 'x'
# Written to possibly share internal code with external contractors.
# Probably not a good idea. But I had fun writing it.

import sys
import re
import string

keyword_blob = """ 
False      await      else       import     pass
None       break      except     in         raise
True       class      finally    is         return
and        continue   for        lambda     try
as         def        from       nonlocal   while
assert     del        global     not        with
async      elif       if         or         yield
"""

keywords = set([ word for line in keyword_blob.split("\n") for word in line.split(" ") if word])

# let's just pretend
keywords.update(("self",))

words = re.compile(r'([a-zA-Z]{1,})')

uppercase = set(string.ascii_uppercase)

def frobnicate(s):
    chars = list(s)

    for w in words.finditer(s):
        token = w.group()
        if token in keywords:
            continue
        
        for i in range(w.start(), w.end()):
            chars[i] = 'X' if chars[i] in uppercase else 'x'

    return ''.join(chars)

if __name__ == '__main__':
    for infilename in sys.argv[1:]:
        with open(infilename,"r") as infile:
            for s in infile.readlines():
                print(frobnicate(s),end="")


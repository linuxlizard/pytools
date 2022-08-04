#!/usr/bin/env python3

# Parse stdin looking for 4+ digit numbers. Convert the numbers' strings to values with commas.
# e.g.,   "this is a number 1000" -> "this is a number 1,000"
import sys
import re

_debug = 0

number_re = re.compile("[0-9]{4,}")

infile = sys.stdin
for oneline in infile.readlines():
    out_line = oneline

    riter = number_re.finditer(oneline)
    for robj in riter:
        num_s = robj.group(0)
        num = int(num_s)
        num_comma_s = "{:,}".format(num)
        if _debug:
            print(f"nums {num_s} {num} {num_comma_s}")
        out_line = out_line.replace(num_s, num_comma_s, 1)

    print(out_line,end="")
    


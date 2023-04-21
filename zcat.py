#!/usr/bin/env python3
#
# Clone zcat(ish) in Python.
# For platforms with no zcat.
# davep 20230421
#
import sys
import gzip

infilename = sys.argv[1]

with gzip.open(infilename,'r') as f:
    for line in f:
        try:
            print("%s" % line.decode('utf8'), end="")
        except UnicodeDecodeError:
            print("??? %s" % line)


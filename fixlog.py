#!/usr/bin/env python3

# davep 26-Apr-2016 ; fix logfiles coming through html/http (entities are escaped)
# https://stackoverflow.com/questions/2087370/decode-html-entities-in-python-string

import sys
import html

def read_file(infilename):
    with open(infilename, "r") as infile:
        yield from infile.readlines()

def fix_entities(strings):
    for s in strings:
        yield html.unescape(s)

def main():
    infilename = sys.argv[1]

    for line in fix_entities(read_file(infilename)):
        print(line, end="")
        

if __name__=='__main__':
    main()

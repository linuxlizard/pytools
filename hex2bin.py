# davep 20171107 ; convert file of space separated printed hex bytes into a raw
# byte file

import sys
import itertools

# https://docs.python.org/3/library/itertools.html#itertools-recipes
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

def main():
    infilename = sys.argv[1]
    outfilename = sys.argv[2]

    with open(infilename,"r") as infile:
#        for line in infile.readlines():
#            print(line)
#            print(line[7:56].strip())
        hexdump = " ".join([s[7:56].strip() for s in infile.readlines()])

    # block of hex as 2 nibbles separated by spaces
    # .e.g, 18 60 30 14 01 00 ...
    buf = bytes([int(c,16) for c in hexdump.split()])

    # solid block of text (no spaces)
    # e.g., 64886F70D010...
#    for c in grouper(hexdump, 2):
#        print(c)
#    buf = bytes([int(''.join(c),16) for c in grouper(hexdump, 2)])

    with open(outfilename,"wb") as outfile:
        outfile.write(buf)

if __name__ == '__main__':
    main()

#!/usr/bin/python

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/142812
FILTER = "".join([(len(repr(chr(x))) == 3) and chr(x) or "." for x in range(256)])


def dump(src, length=8):
    N = 0
    result = ""
    while src:
        s, src = src[:length], src[length:]
        hexa = " ".join(["%02X" % x for x in s])
        s = "".join([chr(n) for n in s])
        s = s.translate(FILTER)
        result += "%04X   %-*s   %s" % (N, length * 3, hexa, s)
        N += length
    return result


def dumpfile(infile):
    while True:
        buf = infile.read(16)
        if not buf:
            break
        yield dump(buf, 16)

if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        with open(f, "rb") as infile:
            for s in dumpfile(infile):
                print(s)

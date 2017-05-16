#!/usr/bin/python

# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/142812

FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(src, length=8):
    N=0; result=''
    try:
        src = src.decode("ascii")
    except AttributeError:
        pass
    while src:
       s,src = src[:length],src[length:]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       s = s.translate(FILTER)
       result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
       N+=length
    return result

def dump2(src, length=8):
    result=[]
    for i in xrange(0, len(src), length):
       s = src[i:i+length]
       hexa = ' '.join(["%02X"%ord(x) for x in s])
       printable = s.translate(FILTER)
       result.append("%04X   %-*s   %s\n" % (i, length*3, hexa, printable))
    return ''.join(result)

if __name__ == '__main__' :
    s=("This 10 line function is just a sample of python power "
       "for string manipulations.\n"
       "The code is \x07even\x08 quite readable!")

#    print dump(s, 16)
#    print dump2(s, 16 )


#!/usr/bin/env python3

# Roll n of N-sided dice. Because I'm bored.
# 
# Example: roll 3d6 
#          roll 2d20
#          roll 1d10
#          roll 6d4
#
# davep 14-Jul-2015

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random
import re

roll_re = re.compile( "^(\d*)[dD](\d+)$" )

def roll_d6():
    d6 = range(1,6+1)
    print(random.choice(d6))
    
def roll( num_dice, num_sides ) : 
    rolls = [ random.choice(range(1,num_sides+1)) for n in range(num_dice) ]
    print("{0}d{1}: {2}".format( num_dice, num_sides, " ".join( [ str(n) for n in rolls ] ) ) )
    print("sum={0} mean={1}".format(sum(rolls),float(sum(rolls))/len(rolls)))

if len(sys.argv) < 2 : 
    roll(1,6)

for r in sys.argv[1:]:
    robj = roll_re.match(r)
    if not robj : 
        print("bad roll spec \"{0}\"".format(r),file=sys.stderr)
        sys.exit(1)
    num_dice = 1
    if robj.group(1) : 
        num_dice = int(robj.group(1))
    die = int(robj.group(2))
    if die not in ( 4, 6, 8, 10, 12, 20 ) : 
        print("no die exists with num sides={0}!".format(die),file=sys.stderr)
        sys.exit(1)
    roll( num_dice, die )

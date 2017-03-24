#!/usb/bin/env python3

# Read from stdin, sub words with "blah" a la Gary Larson.  Created to be a
# smart-ass.  
#
# davep 19-May-2008
# davep 17-Mar-2016 ; updated to python3 and to be much less stupid 

import sys
import re

def main() :
    infile = sys.stdin
    outfile = sys.stdout

    word_re = re.compile( "[A-Za-z]{3,}" )

    while 1 : 
        line = infile.readline().strip()

        # end of file or error
        if len(line) <= 0 : 
            break

        s = re.sub(word_re, "blah", line)
        print(s)
        
if __name__ == '__main__' :
    main()


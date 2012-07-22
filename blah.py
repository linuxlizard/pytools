#!/usb/bin/python

# Read from stdin, sub words with "blah" a la Gary Larson.  Created to be a
# smart-ass.  
#
# davep 19-May-2008
# $Id: blah.py 417 2008-05-19 15:25:15Z davep $

import sys
import re

def main() :
    infile = sys.stdin
    outfile = sys.stdout

    word_re = re.compile( "[A-Za-z]{3,}" )

    while 1 : 
        line = infile.readline()

        # end of file or error
        if len(line) <= 0 : 
            break

        words = line.split() 

        for w in words : 
            robj = word_re.search( w ) 

            if robj is None : 
                print w, 
            else :
                fields = word_re.split( w )
                print fields[0]+"blah"+fields[1],

        print
        
if __name__ == '__main__' :
    main()


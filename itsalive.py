#!/usr/bin/env python3
#
# Terminal image viewer. Pretty flakey. Terminal support is hit/miss.
#
# Based on and inspired by a Tweet from @climagic.
#
# https://twitter.com/climagic/status/596734639894568960
# while :;do printf "[%d;%dH[48;5;%dm [0m" $(($RANDOM % $LINES)) $(($RANDOM % $COLUMNS)) $(($RANDOM % 216 )); done
#

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")
import random
import fcntl
import termios
import struct
import numpy as np
import scipy.misc
from PIL import Image
import random

# https://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def get_win_size():
    win_size = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ,'1234'))
    return win_size

def termp(infilename):
    win_size = get_win_size()
    # win_size[0] = cols (X)
    # win_size[1] = rows (Y)
    print("win_size={0}".format(win_size))

    img = Image.open(infilename)
    img.load()
    ndata = np.asarray(img,dtype="uint8")
    print(ndata.shape)

    aspect_ratio = ndata.shape[1] / ndata.shape[0]
    print("aspect_ratio={0}".format(aspect_ratio))

    ndata_sz = scipy.misc.imresize(ndata,win_size,'bicubic')
    print(ndata_sz.shape)

    img = Image.fromarray( ndata_sz )
    img.save("sz.tif")

    # [48;2;r;g;b 8-bit pixels.  Xterm works. Gnome term to XQuartz fails. Terminal.app fails.

    # https://en.wikipedia.org/wiki/ANSI_escape_code

    image = np.clip( 16 + 36*(ndata_sz[:,:,0]/51) + 6*(ndata_sz[:,:,1]/51) + ndata_sz[:,:,2]/51, 16, 231 )
#    img = Image.fromarray(np.uint8(image))
#    img.save("216.tif")
#    return
    print("shape={0} dtype={1} min={2} max={3}".format(image.shape, image.dtype, image.min(),image.max()))
#    return
#    image = np.ones((ndata_sz.shape[0],ndata_sz.shape[1]),dtype="uint8") * 16 + 36*1 + 6*5 + 5
#    print("shape={0} dtype={1} min={2} max={3}".format(image.shape, image.dtype, image.min(),image.max()))
#    return

    # map the green channel to the 24 levels of grayscale
    gray = np.clip( 0xe8 + ndata_sz[:,:,1]/10.5, 0xe8, 0xff )

    # % export TERM=xterm-256-color
    # seems to help

    # % tput colors
    # should report '256'

    escape = chr(0x1b)
    for row in range(ndata_sz.shape[0]):
        for col in range(ndata_sz.shape[1]):
            print("{0}[{1};{2}H".format(escape,row,col),end="")

            # WORKS in Xterm, Gnome-terminal
            # export TERM=xterm-256-color
            print("{0}[48;2;{1};{2};{3}m ".format(escape,ndata_sz[row][col][0],
                                ndata_sz[row][col][1], ndata_sz[row][col][2] ),end="")

            # test code to fiddle with 8-bit colors
#            print("{0}[48;2;{1};{2};{3}m ".format(escape,32,64,96),end="")

            # WORKS pretty much everywhere
            # green channel mapped to grayscale
#            print("{0}[48;5;{1}m ".format(escape, int(round(gray[row][col])), end=""))

            # RGB->base-6
#            print("{0}[48;5;{1}m ".format(escape, int(round(image[row][col])), end=""))

            # random
#            print("{0}[48;5;{1}m ".format(escape, random.choice(range(0,216)),end=""))

            print("{0}[0m".format(escape),end="")

if __name__=='__main__':
    infilename = sys.argv[1]
    termp(infilename)


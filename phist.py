#!/usr/bin/env python3
#
# Calculate histogram. Print the bins as '*' scaled to terminal width
# davep 31-Mar-2015

import sys
import numpy as np
from PIL import Image
import fcntl
import termios
import struct
import operator

# https://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def get_win_size():
    win_size = struct.unpack('hh', fcntl.ioctl(0, termios.TIOCGWINSZ,'1234'))
    return win_size

def printf_histogram(infilename,channel_num=None):
    img = Image.open( infilename )
    img.load()
    ndata = np.asarray( img, dtype="int" )

    # TODO handle 16-bpp images
    hist_range = (0,255)
    num_bins = 256

    if channel_num and len(ndata.shape)==3:
        # color image has 3 dimensions
        # grayscale image doesn't have channels so ignore channel number
        histo = np.histogram(ndata[:,:,channel_num].flatten(),range=hist_range,bins=num_bins)[0]
    else:
        histo = np.histogram(ndata.flatten(),range=hist_range,bins=num_bins)[0]

    # normalize data to window width and leave space for the pixel indices
    win_width = get_win_size()[1]
    histo /= histo.max()/(win_width-4)

    for idx,h in enumerate(histo):
        print("{0:03} {1}".format(idx,'*'*int(h)))

if __name__=='__main__':
    infilename = sys.argv[1]
    if len(sys.argv) > 2 : 
        channel_num = int(sys.argv[2])
        printf_histogram(infilename,channel_num)
    else:
        printf_histogram(infilename)


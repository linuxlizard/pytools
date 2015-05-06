#!/usr/bin/python

# davep Jul/Aug 2012

import os
import sys
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

def get_basename( filename ) :
    return os.path.splitext( os.path.split( filename )[1] )[0]

def plotit( data, outfilename, **kargs ) :

    # going to make a 1 row x N column plot
    if len(data.shape)==1 : 
        num_rows = 1
    else : 
        num_rows = data.shape[1]

    # davep 02-Oct-2012 ; bump up the size to accommodate multiple rows
    fig = Figure()
    figsize = fig.get_size_inches()
    fig.set_size_inches( (figsize[0],figsize[1]*num_rows) )

    if "title" in kargs : 
        fig.suptitle(kargs["title"])

    # http://matplotlib.org/faq/howto_faq.html
    # "Move the edge of an axes to make room for tick labels"
    # hspace is "the amount of height reserved for white space between
    # subplots"
    fig.subplots_adjust( hspace=0.40 )

    for i in range(num_rows) : 
        ax = fig.add_subplot(num_rows,1,i+1)
        ax.grid()
        if num_rows==1 :
            column = data 
        else : 
            column = data[ :, i ] 

        fmt = ""
        if "color" in kargs : 
            fmt += kargs["color"]            
        fmt += "+"
        ax.plot(column,fmt)

        if "axis_title" in kargs : 
            title = kargs["axis_title"][i]
            ax.set_title(title)

    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print("wrote", outfilename)

def plot_dat( infilename ) :
    basename = get_basename( infilename )

    data = np.loadtxt( infilename)

    outfilename = "{0}_plot.png".format( basename )
    plotit( data, outfilename )

if __name__ == '__main__' :
    infilename_list = sys.argv[1:]

    for infilename in infilename_list : 
        plot_dat( infilename )


#!/usr/bin/env python3

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import os

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

import imtools

def channel_histograms( data_list, outfilename ) : 
    # going to make a 1 row x N column plot
    num_rows = len(data_list)

    # davep 02-Oct-2012 ; bump up the size to accommodate multiple rows
    fig = Figure()
    figsize = fig.get_size_inches()
    fig.set_size_inches( (figsize[0],figsize[1]*num_rows) )

#    if "title" in kargs : 
#        fig.suptitle(kargs["title"])

    # http://matplotlib.org/faq/howto_faq.html
    # "Move the edge of an axes to make room for tick labels"
    # hspace is "the amount of height reserved for white space between
    # subplots"
    fig.subplots_adjust( hspace=0.40 )

    for i in range(num_rows) : 
        ax = fig.add_subplot(num_rows,1,i+1)
        ax.grid()
        ax.set_xlim(0,256)

#        if num_rows==1 :
#            column = data 
#        else : 
#            column = data[ :, i ] 
#
#        fmt = ""
#        if "color" in kargs : 
#            fmt += kargs["color"]            
#        fmt += "+"
#        ax.plot(column,fmt)
        ax.hist( data_list[i]["ndata"].flatten(), range=(0,255), bins=256 )

        ax.set_title( data_list[i]["name"] )

#        if "axis_title" in kargs : 
#            title = kargs["axis_title"][i]
#            ax.set_title(title)

    canvas = FigureCanvasAgg(fig)
    canvas.print_figure(outfilename)
    print("wrote", outfilename)

def channel_histograms_image( filename_list ):

    data_list = []
    for filename in filename_list : 
        ndata = imtools.load_image(filename)
        if len(ndata.shape) == 3 :
            for i in range(ndata.shape[2]):
                s = "{0} ch={1}".format(filename,i)
                data_list.append( { "ndata":ndata[:,:,i], "name":s } )
        else : 
            assert len(data.shape)==2, len(data.shape)
            data_list.append( { "ndata":ndata, "name":filename} )

    # everyone must be the same size
    for data in data_list[1:] :
        if data["ndata"].shape != data_list[0]["ndata"].shape : 
            sys.exit(1)

    channel_histograms(data_list,"hist.png")

if __name__=='__main__':
    if len(sys.argv) > 1 :
        channel_histograms_image( sys.argv[1:] )


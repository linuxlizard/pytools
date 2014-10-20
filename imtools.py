#!/usr/bin/python

# Move some useful image utility functions into own file.
# davep 02-Oct-2011

import sys
import os
import PIL.Image as Image
import numpy as np

def floatstr( floatnum ) : 
    # the [:4] takes at most 4 chars of the float
    # change the '.' in floats to '_' to make filename easier
    return str(floatnum)[:4].replace(".","_")

def load_image( infilename, **kargs ):
    img = Image.open( infilename ) 
    img.load()

    if "mode" in kargs :
        if kargs["mode"]=="L" and img.mode == "RGB" : 
            # use PIL to convert RGB->L
            img = img.convert( "L" )
        elif kargs["mode"]=="RGB" and img.mode != "RGB" :
            raise Exception( "{0} is not an RGB image".format( infilename ) )

    data = np.asarray( img, dtype=kargs.get("dtype","int32") )

    return data

#def load_image_gray( infilename, dtype="int32" ) : 
#    img = Image.open( infilename ) 
#    img.load()
#
#    if img.mode == "RGB" : 
#        # take the green channel
#        img = img.split()[1]
#
#    data = np.asarray( img, dtype=dtype )
#
#    return data

def save_image_old( npdata, outfilename ) : 
    # clip to [0,255], convert to uint8
    # create monochome ("L") image
    img = Image.fromarray( np.asarray( np.clip(npdata,0,255), dtype="uint8"), "L" )
    img.save( outfilename )
    print( "wrote {0}".format( outfilename ))

def save_image( npdata, outfilename ) : 
    # normalize input range down to [0,255], convert to uint8
    # create monochome ("L") image

    delta = float( npdata.max() - npdata.min() )

    # also does a contrast stretch
    normalized = ((npdata - npdata.min()) / delta) * 255

#    print normalized.min(),normalized.max()

    img = Image.fromarray( np.uint8( normalized ))
    img.save( outfilename )
    print( "wrote {0}".format( outfilename ) )

def clip_and_save( data, outfilename ) : 
    data_uint8 = np.asarray( np.clip( data, 0, 255 ), dtype="uint8" )

    # auto detect of rgb/single plane images, save to proper mode
    shapelen = len(data.shape)
    if shapelen==3 : 
        outimg = Image.fromarray( data_uint8, "RGB" )
    elif shapelen==2 : 
        outimg = Image.fromarray( data_uint8, "L" )
    else :
        raise Exception( 
                "Unknown array shape {0} so cannot make image".format(shapelen) )

    outimg.save( outfilename )
    print( "wrote {0}".format( outfilename ) )

def get_basename( filename ) : 
    return os.path.splitext( os.path.split( filename )[1] )[0]


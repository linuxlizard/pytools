#!/usr/bin/env python3

# fiddling with background removal of dilbert comics using local region
# statistics
# davep 7-Apr-2014

import sys
import PIL.Image as Image
import numpy as np

import imtools
import imgycc

def tiling_1(ndata,tile_size=5):
    # Tile patch across the image, replacing a 5x5 area with the area's mean.
    # Tiling in row major order.

    white_tile = np.ones((tile_size,tile_size),dtype="uint8")*255

    num_rows,num_cols = ndata.shape

    row = 0
    col = 0
    while row < num_rows-tile_size :
        while col < num_cols-tile_size :
            rs = slice(row,row+tile_size)
            cs = slice(col,col+tile_size)
            a = ndata[rs,cs]
            if np.mean(a) > 200 : 
                ndata[rs,cs] = white_tile
#                ndata[row:row+tile_size , col:col+tile_size] = white_tile

            col += tile_size

        col = 0
        row += tile_size

def tiling_2(ndata, tile_size=5):
    # Tile patch across the image, replacing a 5x5 area with the area's mean.
    # Tiling in column major order.

    white_tile = np.ones((tile_size,tile_size),dtype="uint8")*255

    num_rows,num_cols = ndata.shape

    row = 0
    col = 0
    while col < num_cols-tile_size :
        while row < num_rows-tile_size :
            if np.mean(ndata[row:row+tile_size , col:col+tile_size]) > 200 : 
                ndata[row:row+tile_size , col:col+tile_size] = white_tile

            row += tile_size

        row = 0
        col += tile_size

def tile_medians(ndata,tile_size=5):
    # https://stackoverflow.com/questions/16713991/indexes-of-fixed-size-sub-matrices-of-numpy-array?rq=1 

    lenr = ndata.shape[0]/tile_size
    lenc = ndata.shape[1]/tile_size
    out = np.array(
            [ ndata[i*tile_size:(i+1)*tile_size,j*tile_size:(j+1)*tile_size] 
                for (i,j) in np.ndindex(lenr,lenc)
            ] ).reshape(lenr,lenc,tile_size,tile_size)
    return out

def ycc_tiling(rgb,ycc,tile_size=5):

    num_rows,num_cols,num_planes = ycc.shape

    zero_tile = np.zeros((tile_size,tile_size),dtype="float")
    white_tile = np.ones((tile_size,tile_size),dtype="float")*255

    y = ycc[:,:,0]
    # cb yellowish/blueish
    # cr redish/greenish
    cb = ycc[:,:,1]
    cr = ycc[:,:,2]

    row = 0
    col = 0
    while row < num_rows-tile_size :
        while col < num_cols-tile_size :
            rs = slice(row,row+tile_size)
            cs = slice(col,col+tile_size)

            m1 = abs(cr[rs,cs].mean())
            m2 = abs(cr[rs,cs].mean())

#            if 0: 
            if m1 > 1 or m2 > 1 : 
                cr[rs,cs] = zero_tile
                cr[rs,cs] = zero_tile
                y[rs,cs] = white_tile
                rgb[rs,cs,0] = white_tile
                rgb[rs,cs,1] = white_tile
                rgb[rs,cs,2] = white_tile

            col += tile_size

        col = 0
        row += tile_size

    # enhance
    if 0 : 
        ycc[:,:,0] = np.clip(ycc[:,:,0]+20,0,255)
        rgb = imgycc.convert_ycc_to_rgb(ycc)
        imtools.save_image(rgb,"out1.tif")

        ycc[:,:,1] *= 1.5
        rgb = imgycc.convert_ycc_to_rgb(ycc)
        imtools.save_image(rgb,"out2.tif")

        ycc[:,:,2] *= 1.5
        rgb = imgycc.convert_ycc_to_rgb(ycc)
        imtools.save_image(rgb,"out3.tif")

#    ycc[:,:,1] = np.zeros_like(cr)
#    ycc[:,:,2] = np.zeros_like(cb)
#    ycc[:,:,0] = np.ones_like(y) * 255
    imtools.save_image(imgycc.convert_ycc_to_rgb(ycc),"ycc.tif")
    imtools.save_image(rgb,"rgb.tif")

def main():
    infilename = sys.argv[1]

    img = Image.open(infilename)
    img.load()

    rgb_ndata = np.asarray(img,dtype="float")
#    rgb_ndata = np.asarray(img,dtype="uint8")

    r,g,b = rgb_ndata[:,:,0],rgb_ndata[:,:,1],rgb_ndata[:,:,2]

    print( r.shape )
    print( g.shape )
    print( b.shape )

    outfilename = "g.tif"
    imtools.clip_and_save(g,outfilename)

    # r,g,b are winding up read-only.
    g2 = np.copy(g)

    ycc_ndata = imgycc.convert_rgb_to_ycc(rgb_ndata)

    ycc_tiling(rgb_ndata,ycc_ndata,3)

#    tiling_2(g2)
#    tiling_1(g2)
#    tiling_1(g2,3)
    outfilename = "g2.tif"
    imtools.clip_and_save(g2,outfilename)

if __name__=='__main__':
    main()


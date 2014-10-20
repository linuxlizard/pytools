#!/usr/bin/env python3

# Convert image to YCC.
# davep Sep? Oct? 2011
#
# Update to Python3
# davep 11-Apr-2014

import sys
import os
import math
import PIL.Image as Image
import numpy as np

rgb_to_ycc = np.array(  
     (0.2990,  0.5870,  0.1140,
    -0.1687, -0.3313,  0.5000,
     0.5000, -0.4187, -0.0813,)
).reshape( 3,3 )

ycc_to_rgb = np.array( 
    ( 1.0, 0.0, 1.4022,
      1.0, -0.3456, -0.7145,
      1.0, 1.7710, 0, )
).reshape( 3, 3 )

ycc_to_bgr = np.array( 
    ( 1.0,  1.7710,           0, 
      1.0, -0.3456,     -0.7145,
      1.0,     0.0,      1.4022,)
).reshape( 3, 3 )

def floatstr( floatnum ) : 
    # the [:4] takes at most 4 chars of the float
    # change the '.' in floats to '_' to make filename easier
    return str(floatnum)[:4].replace(".","_")

def contrast_enhance( ycc, contrast=1.4 ): 
    ycc_enhanced = np.copy( ycc )
    ycc_enhanced[:,:,1] *= contrast
    ycc_enhanced[:,:,2] *= contrast

    return ycc_enhanced

def brightness_enhance( ycc, brightness=20 ) : 
    ycc_enhanced = np.copy( ycc )
    ycc_enhanced[:,:,0] += brightness
    return ycc_enhanced

def gamma_enhance( ycc, gamma=2.2) : 
    # precalc a constant
    gamma_exp = 1.0/gamma

    ycc_enhanced = np.copy( ycc ) 

    # only Gamma the Y channel
    ycc_enhanced[:,:,0] = 255.0 * np.power( ycc_enhanced[:,:,0] / 255.0, gamma_exp )

    return ycc_enhanced

def convert_ycc_to_rgb( ycc ) : 
    return np.dot( ycc, ycc_to_rgb.T )

def convert_ycc_to_bgr( ycc ) : 
    return np.dot( ycc, ycc_to_bgr.T )
    
def convert_rgb_to_ycc( rgb ) : 
    return np.dot( rgb, rgb_to_ycc.T )

def save_ycc_as_image( ycc, basename ) : 
    # move Cb,Cr planes from [-128,127] to [0,255] 
    img_ycc = np.copy(ycc)
    img_ycc[:,:,1] += 128
    img_ycc[:,:,2] += 128

    img_ycc_uint8 = np.asarray( np.clip( img_ycc, 0, 255 ), dtype="uint8" )

    outimg = Image.fromarray( img_ycc_uint8[:,:,0], "L" )
    outimg.save( "{0}_y.tif".format(basename) )
    outimg = Image.fromarray( img_ycc_uint8[:,:,1], "L" )
    outimg.save( "{0}_cb.tif".format(basename) )
    outimg = Image.fromarray( img_ycc_uint8[:,:,2], "L" )
    outimg.save( "{0}_cr.tif".format(basename) )

    outimg = Image.fromarray( img_ycc_uint8, "RGB" )
    outimg.save( "{0}_ycc.tif".format(basename) )

def clip_and_save( rgb, outfilename ) : 
    rgb_uint8 = np.asarray( np.clip( rgb, 0, 255 ), dtype="uint8" )
    outimg = Image.fromarray( rgb_uint8, "RGB" )
    outimg.save( outfilename )

#def image_enhance( ycc, basename, contrast=1.4, brightness=20 ) :
#    rgb_enhanced = convert_ycc_to_rgb( ycc_contrast_enhance( ycc, contrast ) )
#    rgb_uint8 = np.asarray( np.clip( rgb_enhanced, 0, 255 ), dtype="uint8" )
#    outimg = Image.fromarray( rgb_uint8, "RGB" )
#
#    # the [:4] takes at most 4 chars of the float
#    # change the '.' in floats to '_' to make filename easier
#    contrast_str = str(contrast)[:4].replace(".","_")
#    brightness_str = str(brightness)[:4].replace(".","_")
#
#    outimg.save( "{0}_enhanced_{1}.tif".format(basename,contrast_str) )
#
#    rgb_brightened = convert_ycc_to_rgb( ycc_brightness_enhance( ycc, brightness ) )
#    rgb_uint8 = np.asarray( np.clip( rgb_brightened, 0, 255 ), dtype="uint8" )
#    outimg = Image.fromarray( rgb_uint8, "RGB" )
#    outimg.save( "{0}_brightened_{1}.tif".format(basename,brightness_str) )

def run_brightness( ycc, basename, brightness=20 ) :
    rgb_brightened = convert_ycc_to_rgb( ycc_brightness_enhance( ycc, brightness ) )

    # the [:4] takes at most 4 chars of the float
    # change the '.' in floats to '_' to make filename easier
    brightness_str = str(brightness)[:4].replace(".","_")
    outfilename = "{0}_brightened_{1}.tif".format(basename,brightness_str)

    clip_and_save( rgb_brightened, outfilename )

def run_contrast( ycc, basename, contrast=1.4 ) :
    rgb_enhanced = convert_ycc_to_rgb( ycc_contrast_enhance( ycc, contrast ) )

    outfilename = "{0}_enhanced_{1}.tif".format(basename, floatstr( contrast )) 

    clip_and_save( rgb_enhanced, outfilename )

def gamma_lambda( gamma, maxvalue=255 ) : 
    # precalc a constant
    gamma_exp = 1.0/gamma

    # make sure y/maxvalue is a float
    maxf = float(maxvalue)

    return lambda y : maxf * math.pow( y/maxf, gamma_exp )

def old_enhance_gamma( ycc, basename, gamma=2.2 ) :

#    # precalc a constant
#    gamma_exp = 1.0/gamma
#    g = lambda y : 255 * math.pow( y/255.0, gamma_exp )

    g = gamma_lambda( gamma )
    npg = np.frompyfunc( g, 1, 1 )

    ycc_enhanced = np.copy(ycc)
    y_gamma = npg( ycc[:,:,0] )

    ycc_enhanced[:,:,0] = y_gamma 

    return ycc_enhanced

def run_gamma( ycc, basename, gamma=2.2 ) :
    rgb_enhanced = convert_ycc_to_rgb( gamma_enhance( ycc, gamma ) )
    outfilename = "{0}_gamma_{1}.tif".format(basename,floatstr(gamma))
    clip_and_save( rgb_enhanced, outfilename )

def convert_image_to_ycc( infilename ) : 
    basename = os.path.splitext( os.path.split( infilename )[1] )[0]

    img = Image.open( infilename ) 
    img.load()
    if img.mode != "RGB" : 
        print(( "{0} is not an RGB image.".format( infilename ) ))
        sys.exit(1)

    rgb = np.asarray( img, dtype="float" )

    # convert RGB -> YCC
#    ycc = np.zeros_like( rgb ) 
#    for row in range(rgb.shape[0]):
#        ycc[row] = rgb[row] * rgb_to_ycc.T

    ycc = convert_rgb_to_ycc( rgb )
    np.save( basename+"_ycc", ycc )

    save_ycc_as_image( ycc, basename ) 

    return ycc
    
def main( infilename ) : 
    basename = os.path.splitext( os.path.split( infilename )[1] )[0]
    
    # try to load previous file for speed
    try : 
        ycc = np.load( basename+"_ycc.npy" )
    except IOError as err :
        # convert image to ycc
        ycc = convert_image_to_ycc( infilename )

    clip_and_save( convert_ycc_to_bgr(ycc),"out.tif")
    # davep 09-Jan-2013 ; XXX stop after the conversion
    return

    gamma = 2.2
    run_gamma( ycc, basename, gamma )

    ycc_gamma = gamma_enhance( ycc, gamma )
    ycc_contrast = contrast_enhance( ycc_gamma, 1.4 )
    outfilename = "{0}_gamma_contrast.tif".format( basename )
    clip_and_save( convert_ycc_to_rgb( ycc_contrast ), outfilename )

#    run_contrast( ycc, basename, 2.2 )

#    for contrast in np.linspace( 0, 2, num=30 ) : 
#        run_contrast( ycc, basename, contrast ) 

    for b in np.linspace(-1,1) : 
        contrast = 1.0
        brightness = int(b*127)
#        run_enhance( ycc, basename, contrast, brightness ) 


if __name__== '__main__' : 
    infilename = sys.argv[1]

    main( infilename )


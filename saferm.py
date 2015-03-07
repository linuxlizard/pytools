#!/usr/bin/env python3

# Duplicate OSX/BSD 'rm -P' 
# "Overwrite regular files before deleting them.  Files are overwritten three
# times, first with the byte pattern 0xff, then 0x00, and then 0xff again,
# before they are deleted."
# davep 06-Mar-2015

import sys

# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import itertools
import os
import os.path
import stat

def safe_remove(fullpath,size):
    print("rm filename={0} size={1}".format(fullpath,size))
    os.chmod(fullpath,stat.S_IWUSR|stat.S_IRUSR)
    fd = os.open(fullpath,os.O_RDWR)

    zero_buf = bytearray(size)
    ff_buf = bytearray(itertools.repeat(0xff,size))

    os.write(fd,ff_buf)
    os.fsync(fd)
    os.lseek(fd,0,0)

    os.write(fd,zero_buf)
    os.fsync(fd)
    os.lseek(fd,0,0)

    os.write(fd,zero_buf)
    os.fsync(fd)
    os.lseek(fd,0,0)

    os.close(fd)
        
    os.unlink(fullpath)

def find_files(pathname):
#    print(pathname)

    for filename in os.listdir(pathname): 
        fullpath = os.path.join(pathname,filename)
        statinfo = os.stat(fullpath,follow_symlinks=False)
        numbytes = statinfo.st_size

        mode = statinfo.st_mode
        if stat.S_ISDIR(mode):
            find_files(fullpath)
        elif stat.S_ISREG(mode):
            p,ext = os.path.splitext(filename)
            print(fullpath)
            
def main(): 
#    start_dir = sys.argv[1]
#    find_files(os.path.abspath(start_dir))

    for infilename in sys.argv[1:]:
        statinfo = os.stat(infilename,follow_symlinks=False)
        safe_remove(infilename,statinfo.st_size)
        

if __name__=='__main__':
    main()


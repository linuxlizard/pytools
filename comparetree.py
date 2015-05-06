#!/usr/bin/env python3

# Compare two trees of source files.
#
# Sweep a tree looking for *.[ch] Search a second tree for files of same name.
# Compare the two 
#
# Created to compare a set of files in a slightly different tree to the
# original files.  
#
# davep 06-May-2015 ;  

import sys
# require Python 3.x because reasons
if sys.version_info.major < 3:
    raise Exception("Requires Python 3.x")

import os
import fnmatch
import os.path
import subprocess

def find( starting_dir, glob_pattern ):
    #https://stackoverflow.com/questions/2186525/use-a-glob-to-find-files-recursively-in-python
    matches = []
    for root, dirnames, filenames in os.walk(starting_dir):
      for filename in fnmatch.filter(filenames, glob_pattern ):
          matches.append(os.path.join(root, filename))

    return matches

def make_file_dict(dirname):
    file_dict = {}
    file_list = find( dirname, "*.[ch]" )
    for f in file_list : 
        path,fname = (os.path.split(f))
        if fname in file_dict : 
            file_dict[fname].append( path )
        else:
            file_dict[fname] = [ path ]

    return file_dict

def compare_tree_files(first_dir,second_dir):

    first_file_dict = make_file_dict(first_dir)
    second_file_dict = make_file_dict(second_dir)

    for fname in first_file_dict : 
        if not fname in second_file_dict : 
            src = os.path.join( first_file_dict[fname][0], fname )
            print("missing {0}".format(src),file=sys.stderr)
            continue
        
        for dirname in second_file_dict[fname] : 
            src = os.path.join( first_file_dict[fname][0], fname )
            dst = os.path.join( dirname, fname )
            cmd = [ "diff", "-wub", dst, src ]
#            cmd = [ "diff", "-u", src, dst ]

            subprocess.Popen(cmd,executable="diff",stdout=sys.stdout)

def main(): 
    # second location of files we need to search 
    second_dir = sys.argv[1]

    compare_tree_files( ".", second_dir )

if __name__=='__main__':
    main()


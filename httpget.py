#!/usr/bin/env python3

# Fetch files in parallel. Write to same output file like wget. 
# (No wget on OSX.)
#
# Work in progress!
#
# davep 20-oct-2014

import os
import urllib
from urllib.request import urlopen
from urllib.parse import urlparse
from multiprocessing.dummy import Pool as ThreadPool

url_list = [ 
    "http://download.gnome.org/sources/krb5-auth-dialog/2.91/krb5-auth-dialog-2.91.93.tar.gz",
    "http://download.gnome.org/sources/gnome-system-monitor/2.99/gnome-system-monitor-2.99.3.tar.gz", 
    "http://download.gnome.org/sources/libgtop/2.28/libgtop-2.28.3.tar.gz",
    "http://download.gnome.org/sources/gobject-introspection/0.10/gobject-introspection-0.10.5.tar.gz",
]

def wget(url):
    webfile = urlopen(url)

    # called from pool.map() in get() below
    filename = filename_from_url(webfile.url)

    print("filename={0}".format(filename))
    with open(filename,'wb') as outfile:
        outfile.write(webfile.read())

    return 0

def get( url_list ) : 
    # https://medium.com/@thechriskiehl/parallelism-in-one-line-40e9b2b36148
    pool = ThreadPool(4)
    results = pool.map(wget,url_list)
#    results = pool.map(urlopen,url_list)
    pool.close()
    pool.join()

    return results

def filename_from_url(url): 
    # pull apart a URL to find the filename component
    print("url={0}".format(url))
    o = urlparse(url)
    print("parsed={0}".format(o))
    p = os.path.split(o.path)
    filename = p[1]
    return filename

def main(): 
    # read url_list from file
    with open('tmp.txt','r') as infile:
        url_list = [ f.strip() for f in infile.readlines() ]

    # strip blank lines
    url_list = [ f for f in url_list if len(f)>0 ]

#    print(url_list)
#    return

    file_list = get(url_list)

#    for webfile in file_list : 
#        filename = filename_from_url(webfile.url)
#        print("filename={0}".format(filename))
#        with open(filename,'wb') as outfile:
#            outfile.write(webfile.read())

if __name__=='__main__':
    main()


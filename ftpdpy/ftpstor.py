#!/usr/bin/env python3

# Command line one shot ftp STOR a file to FTP server.
# Written to send files from emebedded linux to simple FTP server.
# Very little error handling/recovery. Quick and dirty code.
#
# davep 20240401

import re
import os
import sys
import socket

# The standard FTP ports
#FTP_PORT = 21
#FTP_DATA_PORT = 20

# For running as non-root user.
FTP_PORT = 2121
FTP_DATA_PORT = 2020

BUFSIZE = 1024

USERNAME = "anonymous"
PASSWORD = "nobody@example.com"

# lifted this code from ftplib.py's parse227()
_port_re = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)')

def txrx(sock, msg):
    # dumb send a message, recv a response
    sock.sendall(msg.encode("utf8"))
    buf = sock.recv(BUFSIZE)
    print(f"recv buf={buf}")
    return buf.decode("utf8")

def parse_passive_response(s):
    # lifted this code from ftplib.py's parse227()
    # note no error checking
    m = _port_re.search(s)
    numbers = m.groups()
    ip = '.'.join(numbers[:4])
    port = (int(numbers[4]) << 8) + int(numbers[5])
    return ip, port
    
def ftp_store_passive(server_ip, filename):
    ctrl_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    ctrl_sock.connect( (server_ip, FTP_PORT) )

    # recv the header
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"recv buf={buf}")

    txrx(ctrl_sock, "USER %s\r\n" % USERNAME)
    txrx(ctrl_sock, "PASS %s\r\n" % PASSWORD)
    txrx(ctrl_sock, "TYPE I\r\n")

    buf = txrx(ctrl_sock, "PASV\r\n")
    ip, port = parse_passive_response(buf)
    data_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    data_sock.connect( (ip, port) )

    txrx(ctrl_sock, "STOR %s\r\n" % os.path.split(filename)[1])

    print(f"sending file...")
    with open(filename, "rb") as infile:
        while True:
            buf = infile.read(BUFSIZE<<2)
            print(f"read bytes={len(buf)}")
            if len(buf) == 0:
                break
            data_sock.sendall(buf)

    data_sock.close()
    txrx(ctrl_sock, "QUIT\r\n")

if len(sys.argv) < 3:
    print("usage: %s server-ipaddress file0 [file1 [file2...]]" % sys.argv[0])
    sys.exit(1)

server_ip = sys.argv[1]
filename_list = sys.argv[2:]

for f in filename_list:
    ftp_store_passive(server_ip, f)


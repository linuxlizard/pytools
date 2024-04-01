#!/usr/bin/env python3

# Command line one shot ftp STOR a file to FTP server.
# Written to send files from emebedded linux to simple FTP server.
#
# davep 20240401

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

def parse_ip(s):
    fields = s.split(".")
    assert len(fields)==4, len(fields)
    return [int(f) for f in fields]

def txrx(sock, msg):
    # dumb send a message, recv a response
    sock.sendall(msg.encode("utf8"))
    buf = sock.recv(BUFSIZE)
    print(f"buf={buf}")

def ftp_store(my_ip, server_ip, filename):
    ctrl_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    data_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    data_sock.bind(('',0))
    data_sock.listen(1)
    data_port = data_sock.getsockname()[1]
    print(f"port={data_port}")

    ctrl_sock.connect( (server_ip, FTP_PORT) )

    # recv the header
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    txrx(ctrl_sock, "USER %s\r\n" % USERNAME)
    txrx(ctrl_sock, "PASS %s\r\n" % PASSWORD)
    txrx(ctrl_sock, "TYPE I\r\n")

    port_arg = ( *parse_ip(my_ip), (data_port >> 8), data_port & 0xff)
    txrx(ctrl_sock, "PORT %d,%d,%d,%d,%d,%d\r\n" % port_arg)

    txrx(ctrl_sock, "STOR %s\r\n" % os.path.split(filename)[1])

    (request_sock,(client_address,client_port)) = data_sock.accept()
    print(f"request={request_sock} client={client_address} port={client_port}")

    print(f"sending file...")
    with open(filename, "rb") as infile:
        while True:
            buf = infile.read(BUFSIZE<<2)
            print(f"read bytes={len(buf)}")
            if len(buf) == 0:
                break
            request_sock.sendall(buf)

    request_sock.close()
#    data_sock.close()

    txrx(ctrl_sock, "QUIT\r\n")

if len(sys.argv) < 4:
    print("usage: %s my-ipaddress server-ipaddress file0 [file1 [file2...]]" % sys.argv[0])
    sys.exit(1)

my_ip = sys.argv[1]
server_ip = sys.argv[2]
filename_list = sys.argv[3:]

for f in filename_list:
    ftp_store(my_ip, server_ip, f)


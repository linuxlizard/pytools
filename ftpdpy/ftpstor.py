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

def ftp_store(my_ip, server_ip, filename):

    ctrl_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    data_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    data_sock.bind(('',0))
    data_sock.listen(1)
    data_port = data_sock.getsockname()[1]
    print(f"port={data_port}")

    ctrl_sock.connect( (server_ip, FTP_PORT) )

    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    ctrl_sock.sendall(("USER %s\r\n" % USERNAME).encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    ctrl_sock.sendall(("PASS %s\r\n" % PASSWORD).encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    ctrl_sock.sendall(("TYPE I\r\n").encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    port_arg = ( *parse_ip(my_ip), (data_port >> 8), data_port & 0xff)
    ctrl_sock.sendall(("PORT %d,%d,%d,%d,%d,%d\r\n" % port_arg).encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

    ctrl_sock.sendall(("STOR %s\r\n" % os.path.split(filename)[1]).encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

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

    ctrl_sock.sendall(("QUIT\r\n").encode("utf8"))
    buf = ctrl_sock.recv(BUFSIZE)
    print(f"buf={buf}")

def main():
    if len(sys.argv) < 4:
        print("usage: %s my-ipaddress server-ipaddress file0 [file1 [file2...]]" % sys.argv[0])
        sys.exit(1)

    my_ip = sys.argv[1]
    server_ip = sys.argv[2]
    filename_list = sys.argv[3:]

    for f in filename_list:
        ftp_store(my_ip, server_ip, f)

if __name__ == '__main__':
    main()


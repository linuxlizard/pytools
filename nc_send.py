# https://stackoverflow.com/questions/1908878/netcat-implementation-in-python
import sys
import socket


def netcat(host, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    s.sendall(content.encode())
    s.shutdown(socket.SHUT_WR)
    while True:
        data = s.recv(4096)
        if not data:
            break
        print(repr(data))
    s.close()


# davep 20170728 ; my code
def main():
    ip_address = sys.argv[1]
    port = int(sys.argv[2])
    infilename = sys.argv[3]

    with open(infilename, "rb") as infile:
        buf = infile.read()

    netcat(ip_address, port, buf)


if __name__ == "__main__":
    main()


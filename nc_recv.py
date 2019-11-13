import sys
import socket

def netcat_active(host, port, outfilename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    with open(outfilename,"wb") as outfile:
        while True:
            data = s.recv(4096)
            if not data:
                break
            outfile.write(data)
            outfile.flush()
    s.close()

def main():
    ip_address = sys.argv[1]
    port = int(sys.argv[2])
    outfilename = sys.argv[3]

    netcat_active(ip_address, port, outfilename)

if __name__=='__main__':
    main()


import sys
import socket

def netcat_passive(port, outfilename):
   srv_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   srv_s.bind(("0.0.0.0",port))
   srv_s.listen(1)
   s,port = srv_s.accept()
   with open(outfilename,"wb") as outfile:
       while True:
           data = s.recv(4096)
           if not data:
               break
           outfile.write(data)
           outfile.flush()
   s.close()
   srv_s.close()

def main():
    port = int(sys.argv[1])
    outfilename = sys.argv[2]

    netcat_passive(port, outfilename)

if __name__=='__main__':
    main()


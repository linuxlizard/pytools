#!/usr/bin/python

import os
import sys
import string
import socket
import stat
import time
import glob
import errno
import select
import logging

import cvtfile

logger = logging.getLogger("ftpd")

def get_filelist( path, filespec ) :
    if filespec :
        if path :
            # Want a list of just filenames.  glob.glob() returns the dir when given 
            # a path so we need to remove the leading path from the filelist.
            filelist = [ x.split("/")[-1] for x in glob.glob(path + "/" + filespec) ]
        else :
            filelist = glob.glob( filespec )
    else :
        filelist = os.listdir( path )
    return filelist

def binls( path, filespec ) :

    filelist = get_filelist( path, filespec )

    formatlist = []
    for f in filelist :
        try : 
            (st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid,
                            st_size, st_atime, st_mtime, st_ctime) = os.stat( os.path.join( path, f ) )
        except OSError as err :
            logging.error("Could not stat \"%s\" : %s", f, err)
        else :
            p = [ '-', '-', '-', '-', '-', '-', '-', '-', '-', '-' ]
            
            if stat.S_ISDIR(st_mode)   : p[0] = 'd'
            elif stat.S_ISCHR(st_mode) : p[0] = 'c'
            elif stat.S_ISBLK(st_mode) : p[0] = 'b'
            elif stat.S_ISLNK(st_mode) : p[0] = 'l'

            if st_mode & stat.S_IRUSR : p[1] = 'r'
            if st_mode & stat.S_IWUSR : p[2] = 'w'
            if st_mode & stat.S_IXUSR : p[3] = 'x'
            if st_mode & stat.S_IRGRP : p[4] = 'r'
            if st_mode & stat.S_IWGRP : p[5] = 'w'
            if st_mode & stat.S_IXGRP : p[6] = 'x'
            if st_mode & stat.S_IROTH : p[7] = 'r'
            if st_mode & stat.S_IWOTH : p[8] = 'w'
            if st_mode & stat.S_IXOTH : p[9] = 'x'

            t = time.strftime("%b %d %H:%M",time.localtime(st_mtime))
            formatlist.append( "%10s %3d %5d %5d %8d %-12s %s" % \
                ("".join(p),st_nlink,st_uid,st_gid,st_size,t,f) )

    return formatlist

def split_file_path( path ) :
    if os.path.isdir(path) :
        return (path,'')
    else :
        return os.path.split(path)

# Major chunks were lifted from Python's ftplib module.

# Magic number from <socket.h>
MSG_OOB = 0x1                           # Process data out of band


# The standard FTP ports
#FTP_PORT = 21
#FTP_DATA_PORT = 20

# For running as non-root user.
FTP_PORT = 2121
FTP_DATA_PORT = 2020

BUFSIZE = 1024

# Exception raised when an error or invalid response is received
class Error(Exception): pass
#class error_reply(Error): pass          # unexpected [123]xx reply
#class error_temp(Error): pass           # 4xx errors
#class error_perm(Error): pass           # 5xx errors
#class error_proto(Error): pass          # response does not begin with [1-5]

class InternalError(Error): 
    pass

class AbnormalStop(Error):
    pass

class error_path( Error ) :
    # Error related to a file or path
    path = ""
    errmsg = ""
    def __init__(self,path,errmsg) :
        self.path = path
        self.errmsg = errmsg

class error_command(Error) : 
    # client sent an unknown command
    cmd = ""
    errmsg = ""
    def __init__(self,cmd,errmsg="") :
        self.cmd = cmd
        self.errmsg = errmsg

# Line terminators (we always output CRLF, but accept any of CRLF, CR, LF)
CRLF = '\r\n'
CR = '\r'
LF = '\n'

# Reply codes from RFC959

# 1yz   Positive Preliminary reply
# 2yz   Positive Completion reply
# 3yz   Positive Intermediate reply
# 4yz   Transient Negative Completion reply
# 5yz   Permanent Negative Completion reply

# x0z   Syntax - These replies refer to syntax errors,
# x1z   Information -  These are replies to requests for information
# x2z   Connections - Replies referring to the control and data connections.
# x3z   Authentication and accounting - Replies for the login process 
# x4z   Unspecified as yet.
# x5z   File system - indicate the status of the Server file system 

# "The third digit gives a finer gradation of meaning in each of
# the function categories, specified by the second digit."

connect_greeting = "Hello from ftpd.py version 1.0.0!"   

class NetFTPd(object) :
    root_dir = None # OS level directory which is the root of our ftp directory.
                    # If not set in __init__, defaults to os.getcwd().
    cwd = []   # current working ftp directory as an array of strings
    ftppath = "/"  # current working ftp directory as a single string
    debugging = 2
    sock = None # control connection socket
    data_sock = None # data connection socket
    type = 'I'  # default file type Image
    mode = 'S'  # default FTP mode Stream
    passive = 0 # default to non-passive mode
    port_ip = None   # string IP address of remote host via PORT command
    port_num = None   # numeric port number of remote host via PORT command

    abnormal_stop = 0  # We select() on our sockets for 1 second and watch 
                       # this variable; when set to 1, we raise an exception
                       # to quit.  I'm trying to keep ftpd.py as portable
                       # as possible and select() with signal() doesn't
                       # work under Win32 AFAIK.

    def __init__(self, request, client_address, client_port, **kargs ):
        self.request = request
        self.client_address = client_address
        self.client_port = client_port

        if 'root_dir' in kargs :
            self.root_dir = kargs['root_dir']
        else:
            self.root_dir = os.getcwd()

    def stop( self ) :
        logging.info("NetFTPd.stop()")
        self.abnormal_stop = 1

    # Internal: "sanitize" a string for printing
    def sanitize(self, s):
        if s[:5].lower() == 'pass ' :
            i = len(s)
            while i > 5 and s[i-1] in '\r\n':
                i = i-1
            s = s[:5] + '*'*(i-5) + s[i:]
        return repr(s)

    # Internal: send one line to the server, appending CRLF
    def putline(self, line):
        line = line + CRLF
        if self.debugging > 1: 
            logger.info( '*put* %s', self.sanitize(line) )
        self.senddata(self.request,line.encode())

    # Internal: return one line from the server, stripping CRLF.
    # Raise EOFError if the connection is closed
    def getline(self):
        line = self.readline()
        if self.debugging > 1:
            logger.info( '*get* %s', self.sanitize(line) )
        if not line: raise EOFError
        if line[-2:] == CRLF: line = line[:-2]
        elif line[-1:] in CRLF: line = line[:-1]
        return line

    # Internal: read a line from socket (look for CRLF).
    # Created this function instead of self.file.readline() so can avoid
    # blocking and can self-die if necessary if outside forces decide this
    # client should be disconnected.
    def readline( self ) :
        line = str()
        while 1 :
            if self.abnormal_stop : 
                raise AbnormalStop
            # wait for data with a one second timeout
            readable_sockets = select.select( [self.request], [], [], 1 )[0]
            if not readable_sockets :
                continue

            c = self.request.recv( 1 ) 
            if not c :
                raise EOFError
            line += c.decode()
            if line[-2:] == CRLF :
                return line 

    def readdata( self, sock, buflen ) :
        data = ""
        while 1 :
            if self.abnormal_stop : 
                raise AbnormalStop
            # wait for data with a one second timeout
            readable_sockets = select.select( [sock], [], [], 1 )[0]
            if not readable_sockets :
                continue

            data = sock.recv( buflen ) 
            if not data :
                raise EOFError
            return data

    def senddata( self, sock, data ) :
        pos = 0
        datalen = len(data)
        while datalen > 0 :
            if self.abnormal_stop : 
                raise AbnormalStop
            # wait for writable socket with a one second timeout
            writable_sockets = select.select( [], [sock], [], 1 )[1]
            if not writable_sockets :
                continue

            # require caller to have encoded the buffer 
            n = sock.send(data)
            data = data[n:]
            datalen -= n

    def get_command( self ) :
        line = self.getline()
        # Is this a command with data or just a command?  Look
        # for <string> <SP>
        if line.find( ' ' ) > 0 :
            (cmd,data) = line.split( " ", 1 )
        else :
            cmd = line
            data = ''
        cmd = cmd.upper()
        if cmd not in self.commands :
            raise error_command(cmd)
        return (cmd,data)

    def error500(self,cmd) :
        if self.debugging :
            logger.info( "? %s ", cmd )
        self.putline( "500 Syntax error, command '" + cmd + "' unrecognized." )

    def make_data_port( self ) :
        self.data_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        
        if self.passive :
            # we will wait for connection
            self.data_sock.bind( ('', 0 ))
            self.data_sock.listen(5)
        else :
            # go get it for ourselves
            self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.data_sock.bind( ('', FTP_DATA_PORT))

    def open_data_port( self ) :
        logger.debug("open_data_port type=%s passive=%s", self.type, self.passive)
        if self.data_sock :
            self.putline( "125 Data connection already open; transfer starting." )
        else :
            self.make_data_port()

            if self.type == 'I' :
                self.putline( "150 Open BINARY mode data connection." ) 
            else :
                self.putline( "150 Open ASCII mode data connection." ) 

        if self.passive :
            (sock,(ipaddr,port)) = self.data_sock.accept()
            logger.debug( "remote ip=%s port=%d",ipaddr,port )
            self.data_sock.close()
            self.data_sock = sock
        else :
            assert self.data_sock
            assert self.port_ip
            assert self.port_num
            logger.debug( "data_sock=%s remote ip=%s port=%d", self.data_sock, self.port_ip, self.port_num )
            self.data_sock.connect( (self.port_ip,self.port_num) )

    def ftp_authenticate( self ) :
        username = None
        authenticated = 0

        while not authenticated :
            try : 
                (cmd,data) = self.get_command()
            except error_command as err :
                self.error500(err.cmd)
            else :
                if cmd == "USER" :
                    password = None
                    # did they give us a username?
                    if not data :
                        self.putline( "530 Please login with USER and PASS." )
                    else :
                        self.putline( "331 User name okay, need password.")
                        username = data

                elif cmd == "PASS" :
                    # did they give us a password?
                    if not data :
                        self.putline( "530 Please login with USER and PASS." )
                    elif not username :
                        self.putline( "332 Need account for login." )
                    else :
                        # FIXME -- verify username/password
                        password = data
                        self.putline( "230 User logged in, proceed." )
                        authenticated = 1

                elif cmd == "QUIT" :
                    authenticated = 0
                    break

        return authenticated

    def chdir( self, dir ) :
        newcwd = []
        if dir[:1] == "/" :
            # absolute path; start from the top
            pass
        else :
            # relative path; start from where we are now
            newcwd.extend(self.cwd)

        path = dir.split( "/" )

        for p in path :
            if p == ".." :
                try :
                    newcwd.pop()
                except IndexError :
                    pass
            elif not p or p == "." :
                # empty component
                pass
            else :
                # go down
                newcwd.append( p )

        # we now have a new cwd; make sure it's valid
        ftppath = "/" + "/".join(newcwd)
        abspath = self.root_dir + ftppath
        logger.debug( "ftppath=%s abspath=%s", ftppath, abspath )
        try :
            st = os.stat( abspath )
        except OSError as e :
            raise error_path( newcwd, "550 Invalid path." )
        if not stat.S_ISDIR(st[stat.ST_MODE]) :
            raise error_path( newcwd, "550 Invalid path." )
            
        self.cwd = newcwd
        self.ftppath = ftppath
        self.abspath = abspath

    def command_noop( self, arg ) :
        self.putline( "200 NOOP command okay." )

    def command_help( self, arg ) :
        self.putline( "502 No help here. :-(" )

    def command_syst( self, arg ) :
        if os.name == 'posix' :
            self.putline( "215 UNIX Type: L8" )
        elif os.name == 'nt' :
            # hardwire a version; don't bother trying to get from OS
            self.putline( "215 Windows_NT version 5.0" )
        else :
            self.putline( "215 Unknown/untested system type" )

    def command_cwd( self, arg ) :
        if not arg :
            raise error_command( "CWD", "501 Missing argument for CWD command." )

        try :
            self.chdir(arg)
        except error_path as e:
            self.putline( "501 Invalid directory." )
        else :
            self.putline( "200 CWD successful." )

    def command_pwd( self, arg ) :
        self.putline( '257 "%s" is the current directory.' % self.ftppath )

    def command_type( self, arg ) :
        if not arg :
            raise error_command( "TYPE", "501 Missing argument for TYPE command." )

        arg = arg.upper()
        logger.debug( "Set type to %s.", arg )
        if arg not in ( 'I', 'A' ) :
            self.putline( "501 Unknown or unimplemented type '" + arg + "'." )
        else :
            self.type = arg
            self.putline( "200 Type set to '" + arg + "'." )

    def command_mode( self, arg ) :
        if not arg :
            raise error_command( "MODE", "501 Missing argument for MODE command." )

        arg = arg.upper()
        logger.debug( "Set mode to %s. ", arg )
        if arg not in ( 'S' ) :
            self.putline( "501 Unknown or unimplemented mode '" + arg + "'." )
        else :
            self.mode = arg
            self.putline( "200 Mode set to '" + arg + "'." )

    def command_passive( self, arg ) :
        logger.debug( "Passive mode enabled." )

        if arg :
            raise error_command( "PASV", "501 Invalid PASV command." )

        self.passive = 1

        if self.data_sock :
            self.data_sock.close()

        # chunks of this from ftplib.py's sendport()
        self.make_data_port()
        port = self.data_sock.getsockname()[1] # Get proper port
        host = self.request.getsockname()[0] # Get proper host
        hbytes = host.split('.')
        pbytes = [repr(port//256), repr(port%256)]
        bytes = hbytes + pbytes
        self.putline( "227 Entering Passive Mode (%s)." % ','.join(bytes) )

    _port_re = None

    def command_port( self, arg ) :
        # lifted this code from ftplib.py's parse227()
        if self._port_re is None:
            import re
            self._port_re = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)')
        m = self._port_re.search(arg)
        if not m:
            self.putline( "501 Invalid PORT command." )  
        else :
            numbers = m.groups()
            self.port_ip = '.'.join(numbers[:4])
            self.port_num = (int(numbers[4]) << 8) + int(numbers[5])

            self.putline( "200 PORT command okay." ) 

            self.passive = 0 

    def command_list( self, arg ) :
        """Get a directory listing like /bin/ls but don't use any 
        external commands for maximum portability and safety."""

        if arg :
            # Split the path part and an optional filespec part from the
            # absolute path. If there is a filespec, use globbing to get the
            # file list ; otherwise return everything.
            abspath = self.ftppath_to_abspath( arg )
            (path,filespec) = split_file_path( abspath )
            filelist = binls( path, filespec )
        else :
            filelist = binls( self.abspath, '' )

        self.open_data_port()

        for f in filelist :
            self.data_sock.send( (f+CRLF).encode() )

        self.data_sock.close()
        self.data_sock = None

        self.putline( "226 Closing data connection." )

    def command_nlst( self, arg ) :

        # "The server will return a list of files and no other information."
        #   RFC959

        if arg :
            abspath = self.ftppath_to_abspath( arg )
            (path,filespec) = split_file_path( abspath )
            filelist = get_filelist( path, filespec )
        else :
            filelist = os.listdir( self.abspath )

        self.open_data_port()

        for f in filelist :
            if os.path.isfile(f) :
                self.data_sock.send( (f+CRLF).encode() )

        self.data_sock.close()
        self.data_sock = None

        self.putline( "226 Closing data connection." )

    def ftppath_to_abspath( self, ftppath ) :
        """Convert a path from the ftp client to a file system
        absolute path based on our root directory."""

        if ftppath[:1] == '/' : 
            p = os.path.normpath( self.root_dir + ftppath )
        else :
            p = os.path.normpath( self.abspath + "/" + ftppath ) 

        logger.debug( "abs path=\"%s\"",p )
        
        # We want to be very careful about not allowing folks out
        # of the sandbox defined by root_dir.
        if not p.startswith( self.root_dir ) :
            # stomp on their head if they try to go out of bounds
            raise error_path( ftppath, "550 Invalid filename or path." )
        return p

    def command_retr( self, arg ) :
        if not arg :
            raise error_command( "RETR", "501 Missing filename argument for RETR command." )

        abspath = self.ftppath_to_abspath( arg )

        # make sure it's a file; don't care about other stat information
        self.file_stat( arg, abspath )

        try :
            if self.type == 'A' :
                f = cvtfile.UnixToDosFile()
                f.open( abspath, 'rb' )
            else :
                f = open( abspath, 'rb' )
        except IOError :
            raise error_path( abspath, "550 Failed to open file for reading." )

        self.open_data_port()

        while 1 :
            buf = f.read( BUFSIZE )
            if len(buf) == 0 :
                break
#            self.data_sock.send( buf )
            self.senddata( self.data_sock, buf )

        f.close()

        self.data_sock.close()
        self.data_sock = None

        self.putline( "226 Closing data connection." )

    def command_stor( self, arg ) :
        if not arg :
            raise error_command( "STOR", "501 Missing filename argument for STOR command." )

        ftppath = arg
        abspath = self.ftppath_to_abspath( ftppath )
        (path,filespec) = split_file_path( abspath )
        logger.debug("STOR %s %s", path, filespec)

        # If the target exists, make sure it's a file.  If the target doesn't
        # exist, not a big deal.  Not using self.file_stat() since file_stat()
        # will raise an exception if the file doesn't exist.
        try :
            statinfo = os.stat(abspath)
        except OSError as err :
            if not err.errno == errno.ENOENT :
                logger.error( "! Could not stat \"%s\" : %s", abspath, err )
                raise error_path( abspath, "501 Bad path." )
        else :
            if not stat.S_ISREG(statinfo[stat.ST_MODE]) :
                raise error_path( abspath, "550 \"%s\" is not a regular file." % arg )

        # TODO - refuse to overwrite existing file

        try :
            if self.type == 'A' :
                if sys.platform == 'win32' :
                    # save with CRLF line endings
                    logging.debug("Dosfile")
                    f = cvtfile.DosToUnixFile()
                else :
                    # save with LF line endings
                    logging.debug("Unixfile")
                    f = cvtfile.UnixToDosFile()
                f.open( abspath, 'wb' )
            else :
                f = open( abspath, 'wb' )
        except IOError :
            raise error_path( abspath, "550 Failed to open file for writing." )

        logger.debug("opening data port...")
        self.open_data_port()

        while 1 :
#            buf = self.data_sock.recv(BUFSIZE)
            try :
                buf = self.readdata( self.data_sock, BUFSIZE )
            except EOFError :
                # end-of-file means client has stopped sending us data so we're done.
                break
            f.write( buf )

        f.close()

        self.data_sock.close()
        self.data_sock = None

        self.putline( "226 Closing data connection." )

    def _dir_exists(self, abspath):
        # verify abspath exists and is a directory
        # raises exceptions if exists and is NOT a directory

        if not os.path.exists(abspath):
            return False

        try:
            statinfo = os.stat(abspath)
        except OSError as err :
            logger.error( "! Could not stat \"%s\" : %s", abspath, err )
            raise error_path("failed to stat \"%s\"", ftppath)

        # if it exists and is not a directory, raise an error
        if not stat.S_ISDIR(statinfo[stat.ST_MODE]) :
            logger.info("!\"%s\" already exists and is not a directory", abspath)
            raise error_path("\"%s\" already exists and is not a directory", ftppath)

        return True

    def command_mkdir(self, arg):
        # davep 20-Apr-2016 ; adding mkdir
        # holy crap 13 years since I updated this code 
        if not arg :
            raise error_command( "MKD", "501 Missing argument for MKD command." )

        ftppath = arg
        abspath = self.ftppath_to_abspath(ftppath)

        # will raise exception if abspath exists but isn't a directory
        if self._dir_exists(abspath):
            self.putline( "212 \"%s\" already exists" % ftppath)
            return

        logger.debug( "create dir \"%s\"", abspath)

        try:
            os.mkdir(abspath)
        except OSError as err:
            logger.error( "! failed to mkdir \"%s\" : %s", abspath, err )
            raise error_command("MKD", "504 failed to create dir")

        self.putline( "212 Successfully created %s." % ftppath)

    def command_rmdir(self, arg):
        # davep 20-Apr-2016 ; adding rmdir 
        if not arg :
            raise error_command( "MKD", "501 Missing argument for RMD command." )

        ftppath = arg
        abspath = self.ftppath_to_abspath(ftppath)

        # will raise exception if abspath exists but isn't a directory
        if not self._dir_exists(abspath):
            self.putline( "212 \"%s\" does not exist" % ftppath)
            return

        logger.debug( "remove dir \"%s\"", abspath)

        try:
            os.rmdir(abspath)
        except OSError as err:
            logger.error( "! failed to rmdir \"%s\" : %s", abspath, err )
            raise error_command("RMD", "504 failed to remove dir")

        self.putline( "212 Successfully removed %s." % ftppath)

    def command_dele(self, arg):
        # davep 20-Apr-2016 ; adding dele (unlink file) 
        if not arg :
            raise error_command( "DELE", "501 Missing argument for DELE command." )

        ftppath = arg
        abspath = self.ftppath_to_abspath(ftppath)

        if not os.path.exists(abspath):
            self.putline( "213 \"%s\" does not exist" % ftppath)
            return

        try :
            statinfo = os.stat(abspath)
        except OSError as err :
            logger.error( "! Could not stat \"%s\" : %s", abspath, err )
            raise error_path( abspath, "501 Bad path." )
        if not stat.S_ISREG(statinfo[stat.ST_MODE]) :
            raise error_path( abspath, "550 \"%s\" is not a regular file." % ftppath )

        logger.debug( "unlink file \"%s\"", abspath)

        try:
            os.unlink(abspath)
        except OSError as err:
            logger.error("!could not unlink \"%s\" : %s", abspath, err)
            raise error_path( abspath, "550 \"%s\" failed to unlink" % ftppath)

        self.putline("213 \"%s\" removed" % ftppath)

    def command_cdup(self, arg):
        # davep 20-Apr-2016 ;  adding CDUP
        self.chdir("..")
        self.putline( '257 "%s" is the current directory.' % self.ftppath )

    def command_quit(self, arg):
        # davep 20-Apr-2016 ;  
        self.putline('200 bye!')

    def file_stat( self, ftppath, abspath ) :
        try :
            statinfo = os.stat(abspath)
        except OSError as err :
            logger.error( "! Could not stat \"%s\" : %s", abspath, err )
            raise error_path( abspath, "550 Failed to stat \"%s\"." % ftppath )

        if not stat.S_ISREG(statinfo[stat.ST_MODE]) :
            raise error_path( abspath, "550 \"%s\" is not a regular file." % ftppath)
        
        return statinfo


    def command_feat( self, arg ) :
        if arg :
            raise error_command( "FEAT", "501 Incorrect paramters for FEAT command." )

        self.putline( "211-Features supported" )
        self.putline( " SIZE" )
        self.putline( " MDTM" )
        self.putline( "211 End" )

    def command_size( self, arg ) :
        if not arg :
            raise error_command( "SIZE", "501 Missing filename argument for SIZE command." )

        abspath = self.ftppath_to_abspath( arg )
        statinfo = self.file_stat( arg, abspath )
        self.putline( "213 %d" % statinfo[stat.ST_SIZE] )

    def command_mdtm( self, arg ) :
        if not arg :
            raise error_command( "MDTM", "501 Missing filename argument for MDTM command." )

        abspath = self.ftppath_to_abspath( arg )
        statinfo = self.file_stat( arg, abspath )
        mtime = statinfo[ stat.ST_MTIME ]

        self.putline( "213 %s" % time.strftime( "%Y%m%d%H%M%S", time.localtime(mtime)) )

    command_functions = { # rfc959
                          "NOOP" : command_noop,
                          "HELP" : command_help,
                          "SYST" : command_syst,
                          "CWD"  : command_cwd,
                          "PWD"  : command_pwd,
                          "TYPE" : command_type,
                          "MODE" : command_mode,
                          "PASV" : command_passive,
                          "PORT" : command_port,
                          "LIST" : command_list,
                          "NLST" : command_nlst,
                          "RETR" : command_retr,
                          "STOR" : command_stor,
                          "MKD"  : command_mkdir,
                          "RMD"  : command_rmdir,
                          "DELE" : command_dele,
                          "CDUP" : command_cdup,
                          "QUIT" : command_quit,

                          # rfc2389
                          "FEAT" : command_feat,

                          # draft-ietf-ftpext-mlst-16.txt
                          "SIZE" : command_size,
                          "MDTM" : command_mdtm,
                        }
    commands = list(command_functions.keys()) + ["USER", "PASS"]
#    [commands.append( x ) for x in [ "USER", "PASS" ] ]

    def serveit( self ) :
        """The Main Event."""

#        self.root_dir = os.getcwd()
        self.abspath = self.root_dir

#        # some of the ftplib functions want a file object
#        self.file = self.request.makefile('rb')

        # Welcome to the show, come inside, come inside.
        self.putline( "220 " + connect_greeting )
        
        if not self.ftp_authenticate() :
            return

        while 1 :
            try :
                (cmd,data) = self.get_command()
            except error_command as err :
                self.error500( err.cmd ) 
            else :
                try :
                    self.command_functions[cmd](self,data)
                except KeyError :
                    self.error500( cmd ) 
                except (error_path,error_command) as err :
                    # user sent us a valid command which for some reason we
                    # don't like; send back the error message and wait for
                    # another command
                    self.putline( err.errmsg )

                if cmd == "QUIT" :
                    break

    # For BaseRequestHandler()
    def setup(self) :
        logger.debug( "NetFTPd.setup()" )

    # For BaseRequestHandler()
    def handle( self ) :
        logger.info( "client_address=%s", self.client_address )

        try :
            self.serveit()
        except EOFError :
            logger.info( "Client terminated connection." )
        except socket.error as err :
            logger.error( "Network error from client=%s: err=%d msg=%s", self.client_address, err.errno, err.strerror)

    # For BaseRequestHandler()
    def finish(self) :
        logger.info( "NetFTPd.finish()" )
        try:
            self.request.shutdown(2)
        except OSError:
            # shutdown can fail if remote side died
            pass
        finally:
            self.request.close()

class FTPThread(object) :
    def __init__( self, request, handler_class ) :
        self.request = request
        self.ftpd = None
        self.running = False
        self.handler_class = handler_class

        self.client_address = self.request.getpeername()[0]
        self.client_port = self.request.getpeername()[1]

    def Start(self):
        self.running = True
        import _thread
        _thread.start_new_thread(self.Run, ())

    def Stop(self):
        logging.debug("FTPThread.Stop()")
        if self.ftpd :
            self.ftpd.stop()

    def IsRunning(self):
        return self.running

    def Run(self):
        logging.debug("FTPThread.Run()")

        self.ftpd = self.handler_class( self.request, self.client_address, self.client_port )
        self.ftpd.setup()
        try :
            self.ftpd.handle()
        except :
            logger.exception('Exception happened during processing of request from %s',self.client_address)
        finally:
            self.ftpd.finish()
            del self.ftpd
            self.ftpd = None

        self.running = False
        logging.debug("FTPThread.Run() leaving")

def sync_server( s ) :
    """A synchronous, blocking FTP server."""
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind( ('', FTP_PORT))
    s.listen(5)

    while 1 :
        (request,(client_address,client_port)) = s.accept()
        ftpd = NetFTPd( request, client_address, client_port )
        ftpd.setup()
        ftpd.handle()
        ftpd.finish()
        del ftpd


if __name__ == '__main__' :
    logging.basicConfig(level=logging.DEBUG)

    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind( ('', FTP_PORT))
    s.listen(5)

    thd = None

    while 1 :
        logging.debug("ftpd running on port %d" % FTP_PORT)
        (request,(client_address,client_port)) = s.accept()
        if thd :
            thd.Stop()
            while thd.IsRunning() :
                logging.debug("waiting for thread to die...")
                time.sleep(1)
            del thd

        thd = FTPThread( request, NetFTPd )
        thd.Stop()
        thd.Start()


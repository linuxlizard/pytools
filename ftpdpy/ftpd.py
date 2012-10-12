#!/usr/bin/python

import os
import sys
import string
import socket
import stat
import dircache
import time
import glob
import errno
import select

import cvtfile

def get_filelist( path, filespec ) :
    if filespec :
        if path :
            # Want a list of just filenames.  glob.glob() returns the dir when given 
            # a path so we need to remove the leading path from the filelist.
            filelist = [ x.split("/")[-1] for x in glob.glob(path + "/" + filespec) ]
        else :
            filelist = glob.glob( filespec )
    else :
        filelist = dircache.listdir( path )
    return filelist

def binls( path, filespec ) :

    filelist = get_filelist( path, filespec )

    formatlist = []
    for f in filelist :
        try : 
            (st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid,
                            st_size, st_atime, st_mtime, st_ctime) = os.stat( os.path.join( path, f ) )
        except OSError,err :
            print "Could not stat \"%s\" :" % f, err
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
FTP_PORT = 21
FTP_DATA_PORT = 20

# For running as non-root user.
#FTP_PORT = 2121
#FTP_DATA_PORT = 2020

BUFSIZE = 1024

# Exception raised when an error or invalid response is received
class Error(Exception): pass
#class error_reply(Error): pass          # unexpected [123]xx reply
#class error_temp(Error): pass           # 4xx errors
#class error_perm(Error): pass           # 5xx errors
#class error_proto(Error): pass          # response does not begin with [1-5]
class InternalError(Error): pass

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

class NetFTPd :
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

        if kargs.has_key('root_dir') :
            self.root_dir = kargs['root_dir']
        else:
            self.root_dir = os.getcwd()

    def logit( self, *msg ) :
        print self.client_address,self.client_port,
        for m in msg :
            print m,
        print

    def stop( self ) :
        print "NetFTPd.stop()"
        self.abnormal_stop = 1

    def set_debuglevel(self, level):
        '''Set the debugging level.
        The required argument level means:
        0: no debugging output (default)
        1: print commands and responses but not body text etc.
        2: also print raw lines read and sent before stripping CR/LF'''
        self.debugging = level

    # Internal: "sanitize" a string for printing
    def sanitize(self, s):
        if s[:5].lower() == 'pass ' :
            i = len(s)
            while i > 5 and s[i-1] in '\r\n':
                i = i-1
            s = s[:5] + '*'*(i-5) + s[i:]
        return `s`

    # Internal: send one line to the server, appending CRLF
    def putline(self, line):
        line = line + CRLF
        if self.debugging > 1: 
            self.logit( '*put* %s' % self.sanitize(line) )
#        self.request.send(line)
        self.senddata(self.request,line)

    # Internal: return one line from the server, stripping CRLF.
    # Raise EOFError if the connection is closed
    def getline(self):
#        line = self.file.readline()
        line = self.readline()
        if self.debugging > 1:
            self.logit( '*get* %s' % self.sanitize(line) )
        if not line: raise EOFError
        if line[-2:] == CRLF: line = line[:-2]
        elif line[-1:] in CRLF: line = line[:-1]
        return line

    # Internal: read a line from socket (look for CRLF).
    # Created this function instead of self.file.readline() so can avoid
    # blocking and can self-die if necessary if outside forces decide this
    # client should be disconnected.
    def readline( self ) :
        line = ""
        while 1 :
            if self.abnormal_stop : 
                raise "Abnormal Stop"
            # wait for data with a one second timeout
            readable_sockets = select.select( [self.request], [], [], 1 )[0]
            if not readable_sockets :
                continue

            c = self.request.recv( 1 ) 
            if not c :
                raise EOFError
            line += c
            if line[-2:] == CRLF :
                return line 

    def readdata( self, sock, buflen ) :
        data = ""
        while 1 :
            if self.abnormal_stop : 
                raise "Abnormal Stop"
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
                raise "Abnormal Stop"
            # wait for writable socket with a one second timeout
            writable_sockets = select.select( [], [sock], [], 1 )[1]
            if not writable_sockets :
                continue

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
            self.logit( "? %s " % cmd )
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
            if self.debugging : self.logit( "> remote=",ipaddr,port )
            self.data_sock.close()
            self.data_sock = sock
        else :
            if self.debugging : self.logit( "> remote=", self.port_ip, self.port_num )
            self.data_sock.connect( (self.port_ip,self.port_num) )

    def ftp_authenticate( self ) :
        username = None
        authenticated = 0

        while not authenticated :
            try : 
                (cmd,data) = self.get_command()
            except error_command,err :
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
        self.logit( ftppath, abspath )
        try :
            st = os.stat( abspath )
        except OSError,e :
            raise error_path( newcwd, "550 Invalid path." )
        if not stat.S_ISDIR(st[stat.ST_MODE]) :
            raise error_path( newcwd, "550 Invalid path." )
            
        self.cwd = newcwd
        self.ftppath = ftppath
        self.abspath = abspath

    def command_noop( self, arg ) :
        self.putline( "200 NOOP command okay." )

    def command_help( self, arg ) :
        self.putline( "502 No help here. :-P" )

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
        except error_path,e:
            self.putline( "501 Invalid directory." )
        else :
            self.putline( "200 CWD successful." )

    def command_pwd( self, arg ) :
        self.putline( '257 "%s" is the current directory.' % self.ftppath )

    def command_type( self, arg ) :
        if not arg :
            raise error_command( "TYPE", "501 Missing argument for TYPE command." )

        arg = arg.upper()
        if self.debugging : self.logit( "# Set type to %s."%arg )
        if arg not in ( 'I', 'A' ) :
            self.putline( "501 Unknown or unimplemented type '" + arg + "'." )
        else :
            self.type = arg
            self.putline( "200 Type set to '" + arg + "'." )

    def command_mode( self, arg ) :
        if not arg :
            raise error_command( "MODE", "501 Missing argument for MODE command." )

        arg = arg.upper()
        if self.debugging : self.logit( "# Set mode to %s. "%arg )
        if arg not in ( 'S' ) :
            self.putline( "501 Unknown or unimplemented mode '" + arg + "'." )
        else :
            self.mode = arg
            self.putline( "200 Mode set to '" + arg + "'." )

    def command_passive( self, arg ) :
        if self.debugging : self.logit( "# Passive mode enabled." )

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
        pbytes = [`port/256`, `port%256`]
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
            self.data_sock.send( f+CRLF )

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
            filelist = dircache.listdir( self.abspath )

        self.open_data_port()

        for f in filelist :
            if os.path.isfile(f) :
                self.data_sock.send( f+CRLF )

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

        if self.debugging : self.logit( "> abs path =",p )
        
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

        abspath = self.ftppath_to_abspath( arg )
        (path,filespec) = split_file_path( abspath )

        # If the target exists, make sure it's a file.  If the target doesn't
        # exist, not a big deal.  Not using self.file_stat() since file_stat()
        # will raise an exception if the file doesn't exist.
        try :
            statinfo = os.stat(abspath)
        except OSError,err :
            if not err.errno == errno.ENOENT :
                self.logit( "! Could not stat \"%s\" :" % abspath, err )
                raise error_path( abspath, "501 Bad path." )
        else :
            if not stat.S_ISREG(statinfo[stat.ST_MODE]) :
                raise error_path( abspath, "550 \"%s\" is not a regular file." % arg )

        # TODO - refuse to overwrite existing file

        try :
            if self.type == 'A' :
                if sys.platform == 'win32' :
                    # save with CRLF line endings
                    print "Dosfile"
                    f = cvtfile.DosToUnixFile()
                else :
                    # save with LF line endings
                    print "Unixfile"
                    f = cvtfile.UnixToDosFile()
                f.open( abspath, 'wb' )
            else :
                f = open( abspath, 'wb' )
        except IOError :
            raise error_path( abspath, "550 Failed to open file for writing." )

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

    def file_stat( self, ftppath, abspath ) :
        try :
            statinfo = os.stat(abspath)
        except OSError,err :
            self.logit( "! Could not stat \"%s\" :" % abspath, err )
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

                          # rfc2389
                          "FEAT" : command_feat,

                          # draft-ietf-ftpext-mlst-16.txt
                          "SIZE" : command_size,
                          "MDTM" : command_mdtm,
                        }
    commands = command_functions.keys()
    [commands.append( x ) for x in [ "USER", "PASS", "QUIT" ] ]

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
            except error_command,err :
                self.error500( err.cmd ) 
            else :
                if cmd == "QUIT" :
                    break
                try :
                    self.command_functions[cmd](self,data)
                except KeyError :
                    self.error500( cmd ) 
                except (error_path,error_command),err :
                    # user sent us a valid command which for some reason we
                    # don't like; send back the error message and wait for
                    # another command
                    self.putline( err.errmsg )

    # For BaseRequestHandler()
    def setup(self) :
        self.logit( "NetFTPd.setup()" )

    # For BaseRequestHandler()
    def handle( self ) :
        self.logit( "# client_address=",self.client_address )

        try :
            self.serveit()
        except EOFError :
            self.logit( "# Client terminated connection." )
        except socket.error,err :
            self.logit( "# Network error: %s (%d)" % (err[1],err[0]) )

    # For BaseRequestHandler()
    def finish(self) :
        self.logit( "NetFTPd.finish()" )
        self.request.shutdown(2)
        self.request.close()

class FTPThread :
    def __init__( self, request, handler_class ) :
        self.request = request
        self.ftpd = None
        self.running = False
        self.handler_class = handler_class

        self.client_address = self.request.getpeername()[0]
        self.client_port = self.request.getpeername()[1]

    def Start(self):
        self.running = True
        import thread
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        print "FTPThread.Stop()"
        if self.ftpd :
            self.ftpd.stop()

    def IsRunning(self):
        return self.running

    def Run(self):
        print "FTPThread.Run()"

        self.ftpd = self.handler_class( self.request, self.client_address, self.client_port )
        self.ftpd.setup()
        try :
            self.ftpd.handle()
        except :
            # lifted this from SocketServer
            print '-'*40
            print 'Exception happened during processing of request from',self.client_address
            import traceback
            traceback.print_exc() # XXX But this goes to stderr!
            print '-'*40

        self.ftpd.finish()
        del self.ftpd
        self.ftpd = None

        self.running = False
        print "FTPThread.Run() leaving"

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
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind( ('', FTP_PORT))
    s.listen(5)

    thd = None

    while 1 :
        (request,(client_address,client_port)) = s.accept()
        if thd :
            thd.Stop()
            while thd.IsRunning() :
                print "waiting for thread to die..."
                time.sleep(1)
            del thd

        thd = FTPThread( request, NetFTPd )
        thd.Stop()
        thd.Start()


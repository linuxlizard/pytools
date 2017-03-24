#!/usr/bin/python

"""A wrapper around a file object that will convert the file data during
read/write.  The caller will receive data in a new format, independent of the
data on the disk.  When the caller writes, the data will be converted back to
the original format.  

Use a ConvertFile descendant just as a file handle would be used.  

Currently implemented:
        UnixToDosFile  - Reads a UNIX LF file and returns data as DOS CRLF.
                         Writes data as UNIX LF file.
        DosToUnixFile  - Reads a DOS CRLF file and returns data as UNIX LF.
                         Writes data as a DOS CRLF file.                        
        Rot13File - Reads a plain file and returns data Rot13 encoded.
                    Writes data as Rot13-decoded data.                  

TODO - not a complete file object wrapper yet; there are many many methods
the Python file object has that ConvertFile doesn't.

Originally created as part of an FTP and TFTP server to handle ASCII mode.
"""

# last update 11-Aug-03
VERSION = "1.0.0"

CRLF = '\r\n'
CR = '\r'
LF = '\n'

class ConvertFile(object) :
    buffer = ""
    filename = ""
    file = None
    blocksize = 2048
    eof = 0

    def __init__( self ) :
        self.filename = ""
        self.eof = 1

    def open( self, filename, mode ) :
        self.filename = filename
        self.file = open( self.filename, mode )
        self.eof = 0

    def close( self ) :
        self.file.close()
        self.eof = 1

    def unconvert( self, buffer ) :
        """Convert data from application format back to disk format.
        Designed to be overridden by descendant class."""
        return buffer

    def convert( self, buffer ) :
        """Convert data from format on disk to format given to 
        application.  Designed to be overridden by descendant
        class."""
        return buffer

    def write( self, buffer ) :
        """Write back to file, converting incoming data from the
        new format back to original format."""

        tmpbuf = self.unconvert( buffer )
        return self.file.write( tmpbuf )

    def read( self, buflen ) :
        """Read from file and convert data to a different format."""
        if self.eof :
            return ""

        # FIXME -- should try to dynamically adjust blocksize to be a multiple
        # of buflen.  Currently buflen must be strictly less than our maximum
        # buffer size.
        assert buflen < self.blocksize

        if len(self.buffer) < buflen :
            # read and convert more data into the buffer
            tmpbuf = self.file.read( self.blocksize )
            self.buffer = self.buffer + self.convert( tmpbuf )

        if len(self.buffer) < buflen :
            self.eof = 1
            return self.buffer

        tmpbuf = self.buffer[:buflen]
        self.buffer = self.buffer[buflen:]
        return tmpbuf

class UnixToDosFile( ConvertFile ) :
    """On read, returns Dos format.  On write, saves as UNIX format."""

    last = 0

#    def old_convert( self, buffer ) :
#        # convert LF to CRLF
#        newbuffer = ""
#        chunks = buffer.split( LF )
#
#        lastchunk = len(chunks)-1
#        for i in range(len(chunks)) :
#            c = chunks[i]
#            # if already have CRLF, don't convert
#            if self.last == CR :
#                # last character of previous chunk was a CR
#                newbuffer = newbuffer + c + LF
#            else :
#                # want CRLF between chunks but not
#                # between blocks
#                if i < lastchunk :
#                    newbuffer = newbuffer + c + CRLF
#                else :
#                    newbuffer = newbuffer + c 
#
#            # hang onto last character to find CRLF split across buffers
#            if c :
#                self.last = c[-1]
#            else :
#                self.last = 0
#
#        return newbuffer

    def convert( self, buffer ) :
        """ Convert LF to CRLF except if already a CRLF (don't want CRCRLF)."""
        # Goals:
        #     - inline (convert as caller reads); must convert blocks at a time, 
        #       each block independent of the others
        #     - handle existing CRLF (no CRCRLF; I hate that)
        #     - memory conservative (don't read entire file into memory)
        #     - last but not least, be fast
        #
        # (This turned out a lot harder than I originally thought.)
        #
        # block - 'buffer' parameter; data used in each invocation of convert()
        # chunk - resulting array of strings from a block split by LF

        print("UnixToDosFile.convert()")

        newbuffer = ""
        chunks = buffer.split( LF )

        lastchunk = len(chunks)-1

        if self.last == CR :
            # If last character of previous call was a CR, don't write another
            # CR.  (CRLF split across block boundries; very corner case)

            # If chunks[0] is empty, there was a CRLF split across block
            # boundries.  We already sent out the LF with the CR in the
            # previous block so get rid of this chunk.
            if not chunks[0] :
                chunks = chunks[1:]

        for i in range(len(chunks)) :

            # if already have CRLF, don't convert
            if chunks[i] and chunks[i][-1] == CR :
                # last character is a CR
                newbuffer = newbuffer + chunks[i] + LF
            else :
                # want CRLF between chunks but not between blocks
                if i < lastchunk :
                    newbuffer = newbuffer + chunks[i] + CRLF
                else :
                    newbuffer = newbuffer + chunks[i] 

        # Hang onto last character of last chunk to find CRLF split across
        # blocks.
        if chunks[lastchunk] :
            self.last = chunks[lastchunk][-1]
        else :
            self.last = 0

        return newbuffer

    def unconvert( self, buffer ) :
        # convert CRLF to LF
        return buffer.replace( CR, "" )

class DosToUnixFile( UnixToDosFile ) :
    """On read, returns Unix format.  On write, saves as DOS format."""

    def convert( self, buffer ) :
        return UnixToDosFile.unconvert( self, buffer )

    def unconvert( self, buffer ) :
        return UnixToDosFile.convert( self, buffer )

class Rot13File( ConvertFile ) :

    def convert( self, text ) :
        # rot13 from http://www.miranda.org/~jkominek/rot13/python/rot13.py
        newbuffer = ""
        for c in text:
            print(c)
            byte = ord(c)
            cap = (byte & 32)
            byte = (byte & (~cap))
            if (byte >= ord('A')) and (byte <= ord('Z')):
                byte = ((byte - ord('A') + 13) % 26 + ord('A'))
            byte = (byte | cap)
            newbuffer += chr(byte)

        return newbuffer

    def unconvert( self, text ) :
        return self.convert( text )

if __name__ == '__main__' :
    
    c = UnixToDosFile()
#    c = Rot13File()
    c.open( "rfc959.txt", "rb" )

    f = open( "dos.txt", "w" )
    
    while 1 :
        buf = c.read(512)
        if len(buf) == 0 :
            break
        f.write( buf )

    c.close()
    f.close()

    c.open( "wb" )
    f = open( "dos.txt", "r" )

    while 1 :
        buf = f.read(512)
        if len(buf) == 0 :
            break
        c.write( buf )

    c.close()
    f.close()


#----------------------------------------------------------------------
# This file was generated by \Python22\lib\site-packages\wxPython\tools\img2py.py
#
from wxPython.wx import wxImageFromStream, wxBitmapFromImage
import io


def getData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x0f\x00\x00\x00\x0f\x08\x06\
\x00\x00\x00;\xd6\x95J\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\
\x00AIDATx\x9cc<v\xf8\xd8\x7f\x062\x01\x13\xb9\x1a)\xd6\xcc\x82\xcc\xb1\xb2\
\xb5"\xa8\xe1\xd8\xe1c\x986\xef\xdb\xbf\x8fd\x9b\x07\xce\xcf\xa3\x9aI\x04(\
\x89\xa4\xa5\xa9\x05\xafb\'G\'\x14>\xe3\x80e\x0c\x00\xda\x04\x0eG\xb7\xd8"\
\xc1\x00\x00\x00\x00IEND\xaeB`\x82' 

def getBitmap():
    return wxBitmapFromImage(getImage())

def getImage():
    stream = io.StringIO(getData())
    return wxImageFromStream(stream)



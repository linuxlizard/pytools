#!/usr/bin/python

class foo :
    def __init__( self ) :
        self.foo = "Foo"

    def bar( self ) :
        print id(self)

def logit2( *msg ) :
    for m in msg : 
        print m,
    print

def logit( *msg ) :
    print reduce( lambda x,y : str(x)+" "+str(y), msg )

logit( "foo" )
logit( "foo", "bar" )
logit( "foo", "bar", "baz" )
logit( __name__, 1, 3, logit )

f = foo()
print f
print dir(f)
print id(f)
f.bar()

import os
try:
    os.chdir("foo")
except OSError,e:
    print e
    print dir(e)


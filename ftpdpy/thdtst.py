#!/usr/bin/python

import thread
import time

class FTPThread :

    def Start(self):
        self.keepGoing = True
        self.running = False
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        print "FTPThread.Stop()"
        self.keepGoing = False

    def IsRunning(self):
        print self.running
        return self.running

    def Run(self):
        print "FTPThread.Run()"
        while self.keepGoing :
            time.sleep( 0.5 )
            print( "Run()" )
        self.running = False

f = FTPThread()
f.Start()

for i in range(10) :
    time.sleep(1)
    print "main()"

f.Stop()
while 1 : 
    time.sleep(1)
    print "main() again"


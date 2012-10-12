#!/usr/bin/python

# simple program to learn how to use wx.Socket

import wx

class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):
        # First, call the base class' __init__ method to create the frame
        wx.Frame.__init__(self, parent, id, title, 
                    wx.Point(100, 100), wx.Size(500, 600) )

        textID = wx.NewId()
        self.t1 = wx.TextCtrl(self, textID, "", 
                style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY, 
                pos=wx.DefaultPosition, size=wx.DefaultSize )

        self.sid = wx.NewId()
        addr = wx.IPV4address( )
#        self.sock = wx.SocketServer(  ) 

    def OnSocketInput( self, event ) :
        print "OnSocketInput()"

    def OnSocketOutput( self, event ) :
        print "OnSocketOutput()"

    def OnSocketConnection( self, event ) :
        print "OnSocketConnection()"

    def OnSocketLost( self, event ) :
        print "OnSocketLost()"


class MyApp(wx.App):

    # wxWindows calls this method to initialize the application
    def OnInit(self):
    
        wx.InitAllImageHandlers()

        # Create an instance of our customized Frame class
        frame = MyFrame( wx.NULL, -1, "stest")

        frame.Show()

        # Tell wxWindows that this is our main window
        self.SetTopWindow(frame)

        # Return a success flag
        return wx.true

app = MyApp(0)
app.MainLoop()


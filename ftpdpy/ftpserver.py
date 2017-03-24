#!/usr/bin/python2

import sys
import time
import _thread
import wx
import wx.lib.mixins.listctrl
import socket
import select
import os

import ftpd
from functools import reduce

VERSION = "0.0.1"

g_rootwin = None

g_root_dir = "FTP Files"  # subdir under the exe dir to be the FTP root

# lifted the thread/event stuff from the wxPython Demo thread demo.  Changed to 
# support a string instead of a pair of integers.

wxEVT_SYSLOG_MSG = wx.NewEventType()
wxEVT_FTP_STATE_CHANGE = wx.NewEventType()

def EVT_SYSLOG_MSG(win, func):
    win.Connect(-1, -1, wxEVT_SYSLOG_MSG, func)

class SyslogMsgEvent(wx.PyEvent):

    def __init__(self, str):
        wx.PyEvent.__init__(self)
        self.SetEventType(wxEVT_SYSLOG_MSG)
        self.msg = str


def EVT_FTP_STATE_CHANGE(win, func):
    win.Connect(-1, -1, wxEVT_FTP_STATE_CHANGE, func)

FTPSTATE_NEW_CLIENT = 1
FTPSTATE_CLIENT_DISCONNECT = 2
FTPSTATE_COMMAND = 3
FTPSTATE_IDLE = 4

class FTPStateChangeEvent(wx.PyEvent):

    def __init__( self, state, **kargs ):
        wx.PyEvent.__init__(self)
        self.SetEventType(wxEVT_FTP_STATE_CHANGE)
        self.state = state
        self.kargs = kargs

def ftp_state_change( new_state, **kargs ):
    global g_rootwin

    if g_rootwin :
        evt = FTPStateChangeEvent( new_state, **kargs )
        wx.PostEvent( g_rootwin, evt )

def logit( *msg ):
    global g_rootwin

    if g_rootwin :
        evt = SyslogMsgEvent( reduce( lambda x,y: str(x)+" "+str(y), msg ) )
        wx.PostEvent(g_rootwin, evt)

#----------------------------------------------------------------------

class GUINetFTPd( ftpd.NetFTPd ) :

    def __init__(self, request, client_address, client_port, **kargs ):
        global g_root_dir
        datadir = os.path.join( os.getcwd(), g_root_dir )

        ftpd.NetFTPd.__init__( self, request, client_address, client_port, root_dir=datadir )

    def logit( self, *msg ):
        logit( *msg )

    def setup( self ):
        ftp_state_change( FTPSTATE_NEW_CLIENT, ip=self.client_address, instance=id(self) )
        ftpd.NetFTPd.setup( self )

    def finish( self ):
        ftp_state_change( FTPSTATE_CLIENT_DISCONNECT, ip=self.client_address, instance=id(self) )
        ftpd.NetFTPd.finish( self )

    def get_command( self ):
        ftp_state_change( FTPSTATE_IDLE, ip=self.client_address, instance=id(self) )
        (cmd,data) = ftpd.NetFTPd.get_command(self)
        ftp_state_change( FTPSTATE_COMMAND, ip=self.client_address, instance=id(self), cmd=cmd, args=data )
        return (cmd,data)

class ServerThread :
    def Start(self):
        import _thread
        _thread.start_new_thread(self.Run, ())
        self.keepGoing = True
        self.running = False

        # We want to be able to disconnect individual clients; the Run() thread
        # owns the client thread list and is responsible for asking the client
        # thread to stop.  Add an ID to killid_list to have Run() ask it to
        # stop.
        self.killid_lock = _thread.allocate_lock()
        self.killid_list = []

    def Stop(self):
        self.keepGoing = False

    def StopById( self, id ):
        self.killid_lock.acquire()
        self.killid_list.append( id )
        self.killid_lock.release()

    def IsRunning(self):
        return self.running

    def Run(self):
        print("ServerThread.Run()")

        self.running = True

        s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind( ('', ftpd.FTP_PORT))
        s.listen(5)

        thds = []

        logit( "Waiting for connections" )

        while self.keepGoing  :
            readable_sockets = select.select( [s], [], [], 1 )[0]

            if not readable_sockets :
                # FIXME -- convert ServerThread to use wxSocket and events.  
                # This is an ugly hack to allow the GUI thread to ask the
                # server thread to ask a client thread to stop.  Bleah.
                self.killid_lock.acquire()
                if len(self.killid_list) > 0 :
                    for k in self.killid_list :
                        for t in thds :
                            if k == id(t.ftpd) :
                                t.Stop()
                    self.killid_list = []
                self.killid_lock.release()
                continue

            (request,(client_address,client_port)) = s.accept()

            logit( "New connection from", client_address )

            thd = ftpd.FTPThread( request, GUINetFTPd )
            thd.Start()

            thds.append( thd )

            # *Clang!*  Bring out your dead!  *Clang!*
            # Pull finished threads from our thread list.
            not_dead_yet = []
            for t in thds :
                if t.IsRunning() :
                    not_dead_yet.append(t)

            del thds
            thds = not_dead_yet

        s.close()

        # ask all running threads to stop
        print("asking all threads to stop")
        for t in thds :
            if t.IsRunning() :
                t.Stop()

        self.running = False
        print("ServerThread.Run() leaving")

#----------------------------------------------------------------------

class LogViewFrame( wx.Frame ) :

    def __init__(self, parent, ID, title ) :
        wx.Frame.__init__(self, parent, ID, title, wx.Point(100,100), wx.Size(500,300) )

        textID = wx.NewId()
        self.t1 = wx.TextCtrl(self, textID, "ftpdgui.py %s" % VERSION, 
                style=wx.TE_MULTILINE|wx.TE_RICH|wx.TE_READONLY, 
                pos=wx.DefaultPosition, size=wx.DefaultSize )


#----------------------------------------------------------------------

class SettingsDialog( wx.Dialog ) :

    def __init__(self, parent, ID, title,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE) :

        self.udp_port = 0

        wx.Dialog.__init__(self, parent, ID, title, pos, size )

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "UDP Port:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.text = wx.TextCtrl(self, -1, str(self.udp_port), size=(80,-1))
        box.Add(self.text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.text.SetFocus()

        sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        btn = wx.Button(self, wx.ID_OK, " OK ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        wx.EVT_BUTTON( btn, wx.ID_OK, self.OnOKButton)
        

        btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.AddSizer(box, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def OnOKButton(self, event):
        # validate data
        try:
            udp_port = int(self.text.GetLineText(0),10)
            if udp_port <= 0 or udp_port > 65535 :
                raise ValueError 

        except ValueError :
            dlg = wx.MessageDialog( self, "Invalid UDP Port.  The port number should be an integer from 1 to 65535.",
                                      'Error', wx.OK | wx.ICON_ERROR )

            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

#----------------------------------------------------------------------

# from the wxPython Demo's wxListCtrl demo
class TestListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wx.lib.mixins.listctrl.ListCtrlAutoWidthMixin.__init__(self)


class MyFrame(wx.Frame):

    def __init__(self, parent, id, title):
        # First, call the base class' __init__ method to create the frame
        wx.Frame.__init__(self, parent, id, title, 
                    wx.Point(100, 100), wx.Size(500, 600) )

        # toolbar
        self.tb = self.CreateToolBar( wx.TB_HORIZONTAL
                                 | wx.NO_BORDER
                                 | wx.TB_FLAT
                                 | wx.TB_TEXT
                                 )
        import stop
        self.stopbtnid = wx.NewId()
        self.tb.AddSimpleTool( self.stopbtnid, stop.getBitmap(), "Stop", "Stop the FTP Server" )
        wx.EVT_TOOL( self, self.stopbtnid, self.OnToolClick)

        import run
        self.runbtnid = wx.NewId()
        foo = self.tb.AddSimpleTool( self.runbtnid, run.getBitmap(), "Run", "Start the FTP Server" )
#        self.tb.AddTool( self.runbtnid, run.getBitmap(), "Run", "Start the FTP Server" )
        wx.EVT_TOOL( self, self.runbtnid, self.OnToolClick)

        self.tb.Realize()

        foo = self.tb.EnableTool( self.runbtnid, False )
        print(foo,type(foo),dir(foo))

        # status bar
        self.sb = self.CreateStatusBar()
        self.sb.SetStatusText( "Zero clients", 0 )

        # create a menu bar for the frame
        self.menubar = wx.MenuBar()

        # create a simple menu
        menu = wx.Menu()

        # File menu
        # TODO - setttings dialog (currently don't have anything worth setting)
#        settingsID = wx.NewId()
#        menu.Append( settingsID, "&Settings\tAlt-S", "Settings." )
#        wx.EVT_MENU( self, settingsID, self.OnFileSettings )

#        menu.AppendSeparator()

        exitID = wx.NewId()
        menu.Append( exitID, "E&xit\tAlt-X", "Exit the program." )
        wx.EVT_MENU( self, exitID, self.OnFileExit )

        self.menubar.Append( menu, "&File" )

        # Edit menu
        menu = wx.Menu()

        logID = wx.NewId()
        menu.Append( logID, "Log", "Bring up the Log Window.", wx.ITEM_CHECK )
        wx.EVT_MENU( self, logID, self.OnWindowLog )

        self.menubar.Append( menu, "&View" )
    
        # Help menu
        menu = wx.Menu()
        helpID = wx.NewId()
        menu.Append( helpID, "About", "About the FTP Server." )
        wx.EVT_MENU( self, helpID, self.OnHelpAbout )
        self.menubar.Append( menu, "&Help" )

        # add the menu bar to the frame
        self.SetMenuBar( self.menubar )

        # main control is a list of active connections
        tID = wx.NewId()
        self.list = TestListCtrl(self, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER)

        self.list.InsertColumn(0, "Client IP", width=200 )
        self.list.InsertColumn(1, "State" )

        # send log messages to ourselves
        global g_rootwin
        g_rootwin = self

        self.ftpthrd = ServerThread()
        self.ftpthrd.Start()

        # log frame defaults to off
        self.logdlg = None

        EVT_SYSLOG_MSG( self, self.OnSyslogMsg )
        EVT_FTP_STATE_CHANGE( self, self.OnFTPStateChange )

        wx.EVT_RIGHT_DOWN(self.list, self.OnRightDown)

        # for wxMSW
        wx.EVT_COMMAND_RIGHT_CLICK(self.list, tID, self.OnRightClick)

        # for wxGTK
        wx.EVT_RIGHT_UP(self.list, self.OnRightClick)

    def OnToolClick( self, event ):
        id = event.GetId()
        logit( "tool %s clicked\n" % id )

        if id == self.stopbtnid :
            if self.ftpthrd.IsRunning():
                print("stopping all threads")
                self.ftpthrd.Stop()
        elif id == self.runbtnid :
            if not self.ftpthrd.IsRunning() :
                print("starting ftp thread")
                self.ftpthrd.Start()

    def OnHelpAbout( self, event ):
        dlg = wx.MessageDialog( self, "Instant FTP Server %s\n\nBugs to davep@portsmith.com" % VERSION,
                                  "About Instant FTP Server", wx.OK | wx.ICON_INFORMATION )
    
        dlg.ShowModal()
        dlg.Destroy()
            

    def OnFileExit(self, *event):
        self.Close()
        self.ftpthrd.Stop()

    def OnRightDown( self, event ):
        self.x = event.GetX()
        self.y = event.GetY()
        item, flags = self.list.HitTest((self.x, self.y))
        if flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)
        event.Skip()

    def OnRightClick(self, event):
        item, flags = self.list.HitTest((self.x, self.y))
        if flags & wx.LIST_HITTEST_ONITEM:

            num_selected = self.list.GetSelectedItemCount()
            assert num_selected > 0

            menu = wx.Menu()
            disconnectid = wx.NewId()
            if num_selected > 1 :
                menu.Append( disconnectid, "Disconnect these clients")
            else:
                menu.Append( disconnectid, "Disconnect this client")

            wx.EVT_MENU( self, disconnectid, self.OnPopupDisconnect )
            self.PopupMenu(menu, wx.Point(self.x, self.y))
            menu.Destroy()

    def OnPopupDisconnect( self, event ):
        print("OnPopupDisconnect()")

        print(self.list.GetSelectedItemCount())

        for i in range(self.list.GetItemCount()) :
            item = self.list.GetItem(i)
#            if item.GetMask() & wx.LIST_MASK_STATE :
#                print "item.GetState() is valid"
#            else :
#                print "item.GetState() is not valid"
            print(i,self.list.GetItemText(i),item.GetData(),hex(self.list.GetItemState(i,wx.LIST_STATE_SELECTED)))
            if self.list.GetItemState(i,wx.LIST_STATE_SELECTED) & wx.LIST_STATE_SELECTED :
                print(item.GetText(),"is selected")    
                self.ftpthrd.StopById( item.GetData() )

    def OnFileSettings( self, event ):

        dlg = wx.MessageDialog( self, "Settings not yet implemented.",
                                  "Coming Soon", wx.OK | wx.ICON_INFORMATION )
    
        dlg.ShowModal()
        dlg.Destroy()
        return 

        dlg = SettingsDialog( self, -1, "Settings", size=wx.Size(350, 200),
                         #style = wxCAPTION | wxSYSTEM_MENU | wxTHICK_FRAME
                         style = wx.DEFAULT_DIALOG_STYLE
                         )
        dlg.CenterOnScreen()
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            pass
#            global g_udp_port 
#
#            busy = wx.BusyInfo( "Stopping Syslog thread..." )
#
#            self.msgthrd.Stop()
#            running = 1
#            while self.msgthrd.IsRunning() :
#                print "wait..."
#                time.sleep(0.1)
#
#            g_udp_port = dlg.udp_port 
#            self.msgthrd.Start()

        dlg.Destroy()

    def OnWindowLog( self, event ) :
        if not self.logdlg :
            self.logdlg = LogViewFrame( self, -1, "FTPd Log" )
            self.logdlg.CenterOnScreen()

            wx.EVT_CLOSE( self.logdlg, self.OnCloseLogWindow )

            self.logdlg.Show()
        else:
            self.logdlg.Close()

    def OnCloseLogWindow( self, event ) :
        print("OnCloseLogWindow()")
        self.logdlg.Destroy()
        self.logdlg = None

    def OnFTPStateChange( self, event ):
        if event.state == FTPSTATE_NEW_CLIENT :
            idx = self.list.InsertStringItem( self.list.GetItemCount(), event.kargs['ip'] )
            self.list.SetItemData( idx, event.kargs['instance'] )
        elif event.state == FTPSTATE_CLIENT_DISCONNECT :
            idx = self.list.FindItemData( -1, event.kargs['instance'] )
            self.list.DeleteItem( idx )
        elif event.state == FTPSTATE_COMMAND :
            idx = self.list.FindItemData( -1, event.kargs['instance'] )
            str = event.kargs['cmd'].upper()

            if str == 'PASS' :
                # don't display the password
                self.list.SetStringItem( idx, 1, str )
            else:                                   
                self.list.SetStringItem( idx, 1, str+" "+event.kargs['args'] )
        elif event.state == FTPSTATE_IDLE :
            idx = self.list.FindItemData( -1, event.kargs['instance'] )
            self.list.SetStringItem( idx, 1, "idle" )
            

    def OnSyslogMsg( self, event ) :
        if self.logdlg :
            if event.msg[-1] == "\n" :
                self.logdlg.t1.AppendText( event.msg )
            else:
                self.logdlg.t1.AppendText( event.msg+"\n" )

#----------------------------------------------------------------------

class MyApp(wx.App):

    # wxWindows calls this method to initialize the application
    def OnInit(self):
    
        wx.InitAllImageHandlers()

        # Create an instance of our customized Frame class
        frame = MyFrame( wx.NULL, -1, "Instant FTP Server %s" % VERSION)

        frame.Show()

        # Tell wxWindows that this is our main window
        self.SetTopWindow(frame)

        # Return a success flag
        return wx.true

# A little initial housekeeping.  If our FTP root directory doesn't already
# exist, create it.  
ok = 1
try:
    os.chdir( g_root_dir )
    # if we get here, go back where we were
    os.chdir( ".." )
except OSError as e:
    ok = 0

if not ok :
    try:
        ok = 1
        os.mkdir( g_root_dir )
    except OSError as e:
        startup_error_msg = "I was unable to create the FTP server's file directory.\n\
The operating system reported \"%s\"." % e.strerror
        ok = 0

if ok :
    app = MyApp(0)
else:
    app = wx.PySimpleApp()
    dlg = wx.MessageDialog( None, "%s\n\nFTP Server must exit." % startup_error_msg,
                              'Error', wx.OK | wx.ICON_ERROR )
    dlg.ShowModal()
    dlg.Destroy()

app.MainLoop()


#!/usr/bin/python
import proxysetter
import os
import sys
from socks5server import Socks5ServerDaemon
from socks5client import Socks5ClientDaemon

def printhelp(s):
    print s
    print "usage %s client|server start|stop|restart" % argv[0]
    print "------------------------------"
    setter = proxysetter.create_setter()
    mospclient = Socks5ClientDaemon(setter)
    clientstate = mospclient.getstate()
    if clientstate:
        print "mosp client is running"
    else:
        print "mosp client is NOT running"

    mospserver = Socks5ServerDaemon()
    serverstate = mospserver.getstate()
    if serverstate:
        print "mosp server is running"
    else:
        print "mosp client is NOT running"

if __name__ == "__main__":
    if os.geteuid() != 0:
        print "Please run this service as root."
        os._exit(1)
    argv = sys.argv
    if len(argv) == 3:
        if 'client' == argv[1]:
            setter = proxysetter.create_setter()
            mospclient = Socks5ClientDaemon(setter)
            if 'start' == argv[2]:
                mospclient.start()
            elif 'stop' == argv[2]:
                mospclient.stop()
            elif 'restart' == argv[2]:
                mospclient.restart()
            else:
                printhelp("Unknown command")
        elif 'server' == argv[1]:
            mospserver = Socks5ServerDaemon()
            if 'start' == argv[2]:
                mospserver.start()
            elif 'stop' == argv[2]:
                mospserver.stop()
            elif 'restart' == argv[2]:
                mospserver.restart()
            else:
                printhelp("Unknown commmand")
        else:
            printhelp("Unknown command")
    else:
        printhelp("Unknown command")

    

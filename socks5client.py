#!/usr/bin/python
import socket
import struct
import threading
import select
import SocketServer
import os
from securesocket import *
from const import *
from common import *
from daemon import Daemon

history = {}
semaphore = threading.BoundedSemaphore(1)
def get_history(ip):
    if ip not in history:
        return None
    ret = history[ip]
    return ret
def set_history(ip, data):
    semaphore.acquire()
    history[ip] = data
    semaphore.release()
def is_sensitive(addr):
    for i in sensitive_words:
        if i in addr:
            return True
    return False

class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): pass

class Socks5Client(SocketServer.StreamRequestHandler):

    allow_reuse_address = True

    def connect_remote(self, id, addr, result):
        result[id] = create_socket(addr, secure=True)

    def asyn_do(self, target, args):
        for i in xrange(self.cnt):
            self.threads[i] = threading.Thread(target=target, args=eval(args))
            self.threads[i].start()
        self.wait_threads()
        
    def wait_threads(self):
        for i in xrange(len(self.threads)):
            if self.threads[i]:
                self.threads[i].join()

    def auth(self, id, data, result):
        if not self.remote[id]: return
        self.remote[id].sendall(data)
        result[id] = self.remote[id].recvall(2)
        '''
        print "Auth send:",
        printbytes(data)
        print "Auth recv:",
        printbytes(result[id])
        '''

    def handle_request(self, id, data, result, tictoc):
        tic = time.time()
        if not self.remote[id]: return
        self.remote[id].sendall(data)
        result[id] = self.remote[id].recvall(4)
        if result[id][1] == b'\x00':
            result[id] += self.remote[id].recvall(6)
        tictoc[id] = time.time() - tic
        '''
        print "Req send:", 
        printbytes(data) 
        print "Req recv:",
        printbytes(result[id])
        '''

    def close_one_remote(self, i):
        if self.remote[i]:
            self.remote[i].close()
        self. remote[i] = None

    def evaluate_result(self, errormsg):
        ret = (False, "")
        for i in xrange(len(self.result)):
            if self.result[i] and ord(self.result[i][1]) == 0:
                ret = (True, self.result[i])
            else:
                self.close_one_remote(i)
        if ret[0]:
            self.client.sendall(ret[1])
        else:
            raise Exception(errormsg)

    def transfer(self):
        remote = self.remote[0]
        poll = select.poll()
        poll.register(self.client.fileno(), 1)
        poll.register(remote.fileno(), 1)
        while True:
            try:
                r = poll.poll(100000)
                r = [tmp[0] for tmp in r]
            except Exception as e: 
                printexc()
                break
            if len(r) == 0: break
            if self.client.fileno() in r:
                if remote.send(self.client.recv(4096)) <= 0: 
                    break
            if remote.fileno() in r:
                if self.client.send(remote.recv(4096)) <= 0: 
                    break

    def update(self):
        for i in xrange(self.cnt - 1, -1, -1):
            if not self.remote[i]:
                self.remote.remove(self.remote[i])
                self.threads.remove(self.threads[i])
                self.tictoc.remove(self.tictoc[i])
                self.cnt -= 1
    
    def init(self):
        self.cnt = len(serverlist)
        self.remote = [None for i in xrange(self.cnt)]
        self.threads = [None for i in xrange(self.cnt)] 
        self.tictoc = [None for i in xrange(self.cnt)]
    
    def handle(self):
        try:
            self.client = SecureSocket(sock=self.request, secure=False)
            self.init()

            #1.Version
            time.sleep(0.01)
            self.data = self.client.recvall(2)
            self.data += self.client.recvall(ord(self.data[1]))
            if self.data[0] != b'\x05':
                self.client.send(b'\x05\xFF')
                raise Exception("Unsupported version")
            self.client.send(b'\x05\x00')

            #2.Request
            self.data = self.client.recvall(4)
            atyp = ord(self.data[3])
            if atyp == 1:
                addr = self.client.recvall(4)
                self.data += addr 
            elif atyp == 3:
                alen = self.client.recvall(1)
                self.data += alen
                addr = self.client.recvall(ord(alen[0]))
                self.data += addr
            self.data += self.client.recvall(2)

            record = get_history(addr)

            if (record and record[0] > time.time()) or is_sensitive(addr):
                if not record or record[0] <= time.time():
                    record = (time.time() + 365 * 24 * 3600, trustedserver)
                    set_history(addr, record)
                self.remote[0] = create_socket(record[1], secure = True)
                self.update()
                if self.cnt != 0:
                    self.result = [None for i in xrange(self.cnt)]
                    self.handle_request(0, self.data, self.result, self.tictoc)
                    self.evaluate_result("handle request failed")
                    self.update()

            if self.cnt == 0 or not self.remote[0]:
                self.init()
                self.asyn_do(self.connect_remote, "(i, serverlist[i], self.remote)")
                self.update()
                if self.cnt == 0:
                    raise Exception("No server available")
                    
                self.result = [None for i in xrange(self.cnt)]
                self.asyn_do(self.handle_request, "(i, self.data, self.result, self.tictoc)") 
                self.evaluate_result("handle request failed")
                self.update()
                if self.cnt == 0:
                    raise Exception("No server available for %s" % addr)
                # Get fastest one as transfer server
                min_tictoc = 1000000
                ret_id = -1
                for i in xrange(self.cnt):
                    if self.tictoc[i] < min_tictoc:
                        target = self.remote[i].getpeername()
                        min_tictoc = self.tictoc[i]
                        ret_id = i
                if ret_id == -1:
                    raise Exception("Fatal Error when get fastest server")
                for i in xrange(self.cnt):
                    if i != ret_id:
                        self.remote[i].close()
                        self.remote[i] = None
                self.update()
                set_history(addr, (time.time() + 10 * 3600, target))
            
            #3.Transfer
            self.transfer()
            
        except Exception as e:
            printexc()
        finally:
            self.client.close()
            for s in self.remote:
                if s:
                    s.close()


class Socks5ClientDaemon(Daemon):

    def __init__(self, cfg):
        Daemon.__init__(self, pidfile = '/tmp/mosp_client.pid', stdout = "client_stdout.log",
                        stderr = "client_stderr.log")
        self.cfg = cfg

    def run(self):
        threading.stack_size(1024 * 512 * 2)
        socket.setdefaulttimeout(30)
        server = ThreadingTCPServer(('', CLIENTPORT), Socks5Client)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        
        self.cfg.backup()
        self.cfg.modify("127.0.0.1", str(CLIENTPORT))
        print ">> MOSP client start working"
        server_thread.start()

        while self.run:
            time.sleep(1)

        print ">> Client close successfully"

    def terminate(self, signal, param):
        self.run = False
        self.cfg.restore()
        os._exit(0)


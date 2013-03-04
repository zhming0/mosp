import socket
import copy
import time
import struct
from const import *
from common import *

def create_socket(addr, retry=2, timeout=2, secure=False):
    ret = False
    tmp = 0
    sock = None
    while tmp < retry and ret == False:
        try:
            sock = SecureSocket(secure=secure)
            sock.settimeout(timeout * (tmp + 1))
            sock.connect(addr)
        except SecureSocketError as e:
            print "Find fake ip when connecting ", addr
            return None
        except:
            tmp += 1
            if sock: sock.close()
        else:
            sock.settimeout(socket.getdefaulttimeout())
            return sock
    return None

class SecureSocketError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SecureSocket(socket.socket):

    secure = False

    def __init__(self, family=socket.AF_INET, type=socket.SOCK_STREAM, secure=False, sock=None):
        self._parent = super(SecureSocket, self)
        if not sock:
            self._parent.__init__(family, type)
            self._parent.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            self._parent.__init__(_sock=sock)       
        self.secure = secure
        self._send = self.send
        self._recv = self.recv
        delattr(self, "recv")
        delattr(self, "send")
        '''
        self.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 
                                    struct.pack("ii", True, 10))
        '''
    
    def _encode(self, data):
        swap = lambda data: chr((((ord(data) & 240) >> 4) | (ord(data) << 4)) & 255)
        data = list(data)
        data = map(swap, data)
        return ''.join(data)
    
    def _decode(self, data):
        return self._encode(data)

    def connect(self, addr):
        self._parent.connect(addr)
        if self.getpeername()[0] in fakeip:
            raise SecureSocketError("Fakeip")

    def recvall(self, count):
        data = self.recv(count)
        while len(data) < count:
            time.sleep(0.01)
            d = self.recv(count - len(data))
            if not d:
                raise SecureSocketError("Server close connection unexpectedly")
            data = data + d
        return data
        
    def recv(self, bufsize):
        data = self._recv(bufsize)
        if self.secure: return self._decode(data)
        return data
    
    def send(self, data):
        if self.secure:
            return self._send(self._encode(data))
        return self._send(data)

    def sendall(self, data):
        if self.secure:
            return self._parent.sendall(self._encode(data))
        return self._parent.sendall(data)

if __name__ == "__main__":
    socket.setdefaulttimeout(1)
    ssocket = SecureSocket()
    ssocket.connect(("www.google.com", 80))
    ssocket.sendall("GET / HTTP/1.0\r\n\r\n")
    try:
        print ssocket.recv(4096)
    except SecureSocketError as e:
        print e 
    ssocket.close()


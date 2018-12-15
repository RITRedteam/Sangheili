# Author: Micah Martin (knif3)
# session.py
#
# Handle an incoming SOCKS proxy request
#

import struct
import socket
import select
from socketserver import StreamRequestHandler

from .networking import new_ip, cleanup_ip


# SOCKS Settings
VERSION = 5     # Version 5
METHOD = 0      # No authentication

class SocksSession(StreamRequestHandler):
    def handle(self):
        print('Accepting connection from {}'.format(self.client_address), end="")
        self._src_sock = self.connection
        self._dst_sock = None
        self._remote_addr = None
        self._remote_port = None
        self._outbound_ip = new_ip()
        if self.startSession():
            self.handleSession()

    def startSession(self):
        """Start the SOCKS5 session. This includes unpacking the data sent to the server and making sure
        that the settings are correct. We will only support IPv4 with No authentication

        We implement these settings according to RFC1928
        https://www.ietf.org/rfc/rfc1928.txt

        Returns:
            bool: Whether or not the socks proxy was to our spec.
        """
        # Get the first two bytes from the server and unpack them
        data = self._src_sock.recv(2)
        ver, nmethods = struct.unpack("!BB", data)
        if ver != VERSION:
            self.endSession(0)  # End session with unsupported VERSION
        # Get all the supported client methods
        data = self._src_sock.recv(nmethods)
        methods = set()
        for b in data:
            methods.add(data[b])
        if 0 not in methods:
            self.endSession(0)  # End session with unsupported method
        
        # Choose the method we plan on using and send it back to the server
        reply = struct.pack("!BB", ver, METHOD)
        self._src_sock.sendall(reply)

        # Start figuring out what the client wants to do
        data = self._src_sock.recv(4)
        ver, cmd, _, atype = struct.unpack("!BBBB", data)
        # Get remote addr
        if atype == 1:  # IPv4
            data = self._src_sock.recv(4)
            self._remote_addr = socket.inet_ntoa(data)
        elif atype == 3: # DOMAINNAME
            data = self._src_sock.recv(1)
            length = struct.unpack("!B", data) # Length of domain
            self._remote_addr = self._src_sock.recv(length)
        else:
            self.close()
        # Get remote port
        data = self._src_sock.recv(2)
        self._remote_port = struct.unpack('!H', data)[0]
        # Handle the client command
        try:
            if cmd == 1:  # CONNECT
                self.connectRemote()
                bndaddr, bndport = self._dst_sock.getsockname()
                bndaddr = struct.unpack("!I", socket.inet_aton(bndaddr))[0]
            else:
                self.close()
            reply = struct.pack("!BBBBIH", ver, 0, 0, atype, bndaddr, bndport)
            self._src_sock.sendall(reply)
        except Exception as err:
            print(":", err)
            reply = struct.pack("!BBBBIH", ver, 5, 0, atype, 0, 0) # Return connection refused
            self._src_sock.sendall(reply)
            self.close()
            return False
        return True
    
    def handleSession(self):
        print(" => ('{}', {})".format(self._remote_addr, self._remote_port))
        while True:
            # wait until client or remote is available for read
            r, w, e = select.select([self._src_sock, self._dst_sock], [], [])
            if self._src_sock in r:
                data = self._src_sock.recv(4096)
                if self._dst_sock.send(data) <= 0:
                    break
            if self._dst_sock in r:
                data = self._dst_sock.recv(4096)
                if self._src_sock.send(data) <= 0:
                    break
        self.close()

    def endSession(self, reason=0):
        """End the SOCKS session due to an error."""
        if reason == 0:
            reply = struct.pack("!BB", 0, 255)  # Unsupported version or auth method
        self._src_sock.sendall(reply)
        self.close()

    def connectRemote(self):
        """Try to connect to the remote client. This part is where we choose the outbound
        IP address and randomize the outgoing connection.
        """
        self._dst_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO: GET A RANDOM IP RIGHT HERE
        try:
            self._dst_sock.bind((self._outbound_ip, 0))
            print(" => ({})".format(self._outbound_ip))
        except:
            pass
        self._dst_sock.connect((self._remote_addr, self._remote_port))

    def close(self):
        """Clean up the sockets"""
        if self._src_sock:
            self._src_sock.close()
        if self._dst_sock:
            self._dst_sock.close()
        if self._outbound_ip:
            cleanup_ip(self._outbound_ip) # Cleanup the extra IP address
        self.server.close_request(self.request)

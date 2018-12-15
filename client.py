# Author: Micah Martin (knif3)
#
# client.py
#
# Connects to the Sangheili server to allow tools to proxy through it. Equivilent to nc -x
# This tool also allow us to listen on a localhost port and forward that traffic to the proxy
import sys
import socket
import struct
import argparse

SOCKS_VERSION = 5
SOCKS_METHOD = 0 # No authentication

def setup_sock(rhost, rport, proxyhost, proxyport=1080, lhost="127.0.0.1", lport=None):
    """Setup the SOCKS5 connection to the remote server.

    Args:
        rhost (str): The remote host to connect to
        rport (int): the remote port to connect to
        proxyhost (str): The socks server to connect to
        proxyport (int, optional): the socks port to connect to
        lhost (str, optional): the local host to 
        lport (int, optional): the local port to bind to if provided
    """
    sock = socket.socket()
    if lport and lhost:
        sock.bind((lhost, lport))  # Bind to the local port
    sock.connect((proxyhost, proxyport))  # Connect to the proxy
    data = struct.pack("!BBB", SOCKS_VERSION, 1, SOCKS_METHOD)
    sock.sendall(data)
    data = sock.recv(4096)  # Get the reply from the server
    ver, method = struct.unpack("!BB", data)
    assert ver == SOCKS_VERSION  # Validate server version
    assert method == SOCKS_METHOD  # Validate server method
    data = struct.pack("!BBBBLH", SOCKS_VERSION, 1, 0, 1, socket.inet_aton(rhost), rport)
    sock.sendall(data)
    sock.recv(4096)
    loop_socket(sock)

def loop_socket(sock):
    while True:
        data = sys.stdin.readline(0)
        sock.sendall(data)
        sys.stdout.write(sock.recv(4096))

def main():
    pass

if __name__ == "__main__":
    main()
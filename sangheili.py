# Author: Micah Martin (knif3)
# sangheili
#
# Serve a SOCKS proxy and assign a random IP address to use for the outbound connection
#

from socketserver import ThreadingMixIn, TCPServer

from src.session import SocksSession

class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass

if __name__ == '__main__':
    server = ThreadingTCPServer(('0.0.0.0', 1080), SocksSession)
    server.serve_forever()
    server.server_close()
from socketserver import ThreadingMixIn, TCPServer

from src.session import SocksSession

class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass

if __name__ == '__main__':
    server = ThreadingTCPServer(('0.0.0.0', 1080), SocksSession)
    server.serve_forever()
    server.server_close()
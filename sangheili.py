# Author: Micah Martin (knif3)
# sangheili
#
# Serve a SOCKS proxy and assign a random IP address to use for the outbound connection
#

import yaml
from socketserver import ThreadingMixIn, TCPServer

from src import config
from src.session import SocksSession
from src.networking import net_init

class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    pass

def main():
    # Load the config file
    with open("config.yml") as fil:
        config = yaml.read(fil)
    
    # Set up all the networking stuff
    net_init()

    # Set up the server and start listening
    server = ThreadingTCPServer((config.get("server", "0.0.0.0"), config.get("port", 1080)), SocksSession)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

if __name__ == '__main__':
    main()
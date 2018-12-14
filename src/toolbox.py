# Author: Micah Martin (knif3)
# toolbox.py
#
# Get a random IP address to use for the outbound connection
#

import random
import socket
from ipaddress import IPv4Network


def get_outbound_ip():
    """Build a socket and try to connect to something.
    remote ip doesnt even have to be real
    """
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.connect(("1.1.1.1",1))
    ip = soc.getsockname()[0]
    soc.close()
    return ip


def get_random_ip():
    return random.choice(HOSTS)


IP = get_outbound_ip()
NETMASK = "/24"
HOSTS = [ip.exploded for ip in IPv4Network(IP+NETMASK, strict=False).hosts()]


if __name__ == "__main__":
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
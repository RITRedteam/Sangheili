# Author: Micah Martin (knif3)
# toolbox.py
#
# Get a random IP address to use for the outbound connection
#

import random
import socket
from subprocess import Popen, PIPE
from ipaddress import IPv4Network

NETMASK = "/24"
LABEL = "sangheili"

def addInterface(ip, dev, label=None):
    '''
    add a virtual interface with the specified IP address
    Returns: label - the label of the new interface
    '''
    # Generate a label for the virtual interface
    label = "{}:{}{}".format(dev, LABEL, random.randint(1, 1000))
    while label in getInterfaceLabels(dev):
        label = "{}:{}{}".format(dev, LABEL, random.randint(1, 1000))

    # Add the interface
    command = "ip addr add {}/24 brd + dev {} label {}"
    command = command.format(ip, dev, label)
    res = execute(command)
    if res.get('status', 255) != 0:
        raise Exception("Cannot add interface: {}\n{}".format(
                        res.get('stderr', ''), command))
    return {'label': label, 'ip': ip}


def delInterface(ip, dev):
    '''
    delete a virtual interface with the specified IP address
    '''
    res = execute("ip addr del {}/24 dev {}:*".format(ip, dev))
    if res.get('status', 255) != 0:
        raise Exception("Cannot delete interface: {}".format(
                        res.get('stderr', '')))
    return True

def getInterfaceLabels(dev):
    '''
    return the labels of all virtual interfaces for a dev
    '''
    # The command to list all the labels assigned to an interface
    command = "".join(("ip a show dev {0} | grep -Eo '{0}:[a-zA-Z0-9:]+'",
                       " | cut -d':' -f2-"))
    # command = "ip a show dev {0}"
    command = command.format(dev)
    res = execute(command)
    try:
        labels = res['stdout'].strip().split()
        return labels
    except Exception as E:
        raise Exception("Cannot get labels: {}".format(res.get('stderr', '')))

def getIp(host="1.1.1.1"):
    """Get the ip address that would be used to connect to this host

    Args:
        host (str): the host to connect to, default to an external host
    """
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.connect((host,1))
    ip = soc.getsockname()[0]
    soc.close()
    return ip

def getInterfaceNameFromIp(ip):
    """Given an IP address, return the interface name the is associated with it
    """
    res = execute("ip addr | grep '{}' -B2".format(ip))  # Get three lines of output
    if res.get('status', 255) != 0:
        raise Exception("Cannot find default interface: {}".format(res.get('stderr', '')))
    dev = res['stdout'].split()[-1].strip()
    if dev == "dynamic":
        dev = res['stdout'].split("\n")[0].split()[1].strip(":")
    return dev

def get_random_ip():
    base_ip = getIp()
    interface = getInterfaceNameFromIp(base_ip)
    HOSTS = [ip.exploded for ip in IPv4Network(base_ip+NETMASK, strict=False).hosts()]
    new_ip = random.choice(HOSTS)
    addInterface(new_ip, interface)
    return new_ip

def execute(args):
    '''
    Execute a command. Pass the args as an array if there is more than one
    '''
    retval = {'status': 255}
    try:
        proc = Popen(args, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE,
                     close_fds=True)
        retval['stdout'] = proc.stdout.read().decode("utf-8")
        retval['stderr'] = proc.stderr.read().decode("utf-8")
        retval['status'] = proc.wait()
    except Exception as E:
        print(args)
        print(E)
    return retval

if __name__ == "__main__":
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
    print(get_random_ip())
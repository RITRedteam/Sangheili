# Author: Micah Martin (knif3)
# toolbox.py
#
# Get a random IP address to use for the outbound connection
#

import random
import socket
import struct
from subprocess import Popen, PIPE
from ipaddress import IPv4Network

from . import config
from .arp import isIpTaken, _getIpFromDevice

LABEL = "ark"  # The label that new IPs are created with

## Functions that are to be called by other (sub)modules
def net_init():
    """Set up the networking stuff
    """
    if 'net_device' in config.config:
        config.config['net_base_ip'] = _getIpFromDevice(config.config['net_device'])
    else:
        config.config['net_base_ip'] = _getIp()
        config.config['net_device'] = _getInterfaceNameFromIp(config.config['net_base_ip'])
    config.config['net_netmask'] = _getSubnetMaskFromIp(config.config['net_base_ip'])  # Subnet mask

    _loadHosts()


def new_ip():
    """Get a new, random IP address to use for outbound connections
    """
    new_ip = random.choice(config.config.get('net_addresses'))
    if not config.config.get("reserve_addresses", False):
        _addVirtualInterface(new_ip, config.config.get('net_device'))
    return new_ip


def cleanup_ip(ip):
    """Signal that we are done with an IP address
    """
    # If we are not just saving all the addresses, then delete it
    if not config.config.get("reserve_addresses", False):
        _delVirtualInterface(ip)


## Functions that are used internally not to be called by other modules
def _addVirtualInterface(ip, dev):
    '''
    add a virtual interface with the specified IP address

    Args:
        ip (str): The ip address to add
        dev (str): The dev to add the virtual interface to
    
    Returns:
        dict: the label of the new interface
    '''
    # Generate a label for the virtual interface
    label = "{}:{}{}".format(dev, LABEL, random.randint(1, 1000))
    while label in _getInterfaceLabels(dev):
        label = "{}:{}{}".format(dev, LABEL, random.randint(1, 1000))
    netmask = config.config['net_netmask']
    # Add the interface
    command = "ip addr add {}{} brd + dev {} label {}"
    command = command.format(ip, netmask, dev, label)
    res = execute(command)
    if res.get('status', 255) != 0:
        raise Exception("Cannot add interface: {}\n{}".format(
                        res.get('stderr', ''), command))
    return label


def _delVirtualInterface(ip, dev=None):
    '''
    delete a virtual interface with the specified IP address

    Args:
        ip (str): The ip address of the virtual interface
        dev (str, optional): the dev name
    '''
    if not dev:
        dev = _getInterfaceNameFromIp(ip)
    else:
        dev += ":*"
    netmask = _getSubnetMaskFromIp(ip)
    res = execute("ip addr del {}{} dev {}".format(ip, netmask, dev))
    if res.get('status', 255) != 0:
        raise Exception("Cannot delete interface: {}".format(
                        res.get('stderr', '')))
    return True


def _getInterfaceLabels(dev):
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
    except Exception:
        raise Exception("Cannot get labels: {}".format(res.get('stderr', '')))


def _getIp(host="1.1.1.1"):
    """Get the ip address that would be used to connect to this host

    Args:
        host (str): the host to connect to, default to an external host
    """
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soc.connect((host,1))
    ip = soc.getsockname()[0]
    soc.close()
    return ip


def _getSubnetMaskFromIp(ip):
    """Get the subnet mask for the given IP

    Args:
        ip (str): the ip address
    Returns:
        str: the subnet mask
    """
    res = execute("ip addr | grep -oE '{}/[^ ]+'".format(ip))  # Get three lines of output
    if res.get('status', 255) != 0:
        raise Exception("Cannot find default interface: {}".format(res.get('stderr', '')))
    mask = res['stdout'].split("/")[-1].strip()
    return "/" + mask


def _getInterfaceNameFromIp(ip):
    """Given an IP address, return the interface name the is associated with it

    Args:
        ip (str): the ip address
    Returns:
        str: the interface name
    """
    res = execute("ip addr | grep '{}' -B2".format(ip))  # Get three lines of output
    if res.get('status', 255) != 0:
        raise Exception("Cannot find default interface: {}".format(res.get('stderr', '')))
    dev = res['stdout'].split()[-1].strip()
    if dev == "dynamic":
        dev = res['stdout'].split("\n")[0].split()[1].strip(":")
    return dev


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


def _findHosts():
    # Get all the possible hosts in the network
    hosts = [ip.exploded for ip in IPv4Network(config.config['net_base_ip']+config.config['net_netmask'], strict=False).hosts()]
    random.shuffle(hosts)
    count = config.config.get('address_count', 50)
    print("Discovering {} addresses to use...".format(count))
    addresses = set()
    # Keep looping until we run out of ip addresses or have found enough
    for ip in hosts:
        if ip not in addresses:
            if not isIpTaken(config.config['net_device'], ip):
                addresses.add(ip)
                print(".", end="", flush=True)
        if len(addresses) == count:
            break
    config.config['net_addresses'] = list(addresses)
    print(addresses)
        

def _loadHosts():
    """Figure out which hosts we are allowed to use based on the config.config.
    Update config.config['net_addresses'] with the hosts
    """

    if config.config.get('address_server', False):
        #raise NotImplementedError("'address_server' is not yet implemented")
        from .arkclient import ArkClient, ArkApiError
        client = ArkClient(config.config.get("address_server"))
        client.login("admin", "password")
        addresses = config.config.get("address_count", 30)
        try:
            reg = client.registerHalo("Sangheili", addresses)
        except ArkApiError as E:
            reg = client.getAddresses("Sangheili")
        config.config['net_addresses']= reg['addresses']
        if config.config['net_addresses']:
            print("Loaded addresses from ArkServer '{}'".format(
                  config.config.get("address_server")))
        else:
            raise ValueError("No addresses could be loaded from {}".format(
                  config.config.get("address_server")))

    elif config.config.get('address_file', False):
        #raise NotImplementedError("'address_file' is not yet implemented")
        with open(config.config.get('address_file')) as fil:
            config.config['net_addresses'] = [ip.strip() for ip in fil.readlines()]
    elif config.config.get('address_list', False):
        if not isinstance(config.config['address_list'], list) or not config.config['address_list']:
            raise ValueError("If 'address_list' is specified, it must be a (non-empty) list of ip addresses")
        config.config['net_addresses'] = config.config['address_list']
        del config.config['address_list']
    else:
        # Default to just searching the net for IPs, but warn
        if not config.config.get('address_count', False):
            print("WARN: set a method for gathering ip addresses in 'config.yml'")
        # Find the ip addresses that we are allowed to use from the network itself
        _findHosts()

    # Add all the virtual interfaces
    if config.config.get('reserve_addresses', False):
        for ip in config.config['net_addresses']:
            try:
                _addVirtualInterface(ip, config.config['net_device'])
            except:
                print("WARN: Address exists:", ip)
                pass

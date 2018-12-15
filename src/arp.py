#!/usr/bin/env python3
# Trying to send a receive ARP packets based on these resources:
# https://stackoverflow.com/questions/24415294/python-arp-sniffing-raw-socket-no-reply-packets
# https://github.com/krig/send_arp.py
# http://dk0d.blogspot.com/2016/07/code-for-sending-arp-request-with-raw.html

import fcntl
import socket
import struct
from threading import Thread, Event

from . import config

def isIpTaken(dev, ip):
    '''
    The device to send the ARP to
    '''
    timeout = 0.25
    # initialize the socket to listen on (0x0003)
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    sock.settimeout(timeout)
    isdone = Event() # An event to wait for the listener
    retval = [] # Where to store the return value
    
    # Create the thread and start it
    listener = Thread(target=listen_arp, args=(sock, ip, isdone, retval))
    listener.start()

    # Send an arp packet out
    send_arp(dev, _getIpFromDevice(dev), ip)
    # Wait for the thread or kill it
    isdone.wait(timeout=timeout)
    isdone.set()
    sock.close()
    if retval:
        return True
    else:
        return False


def _getIpFromDevice(device):
    '''
    Given a device name, return the ip for that interface
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = socket.inet_ntoa(fcntl.ioctl(
                                         s.fileno(),
                                         0x8915,  # SIOCGIFADDR
                                         struct.pack('256s', device.encode())
                                         )[20:24])
    s.close()
    return addr


def listen_arp(sock, ip, done, retval):
    '''
    Listen for an ARP reply for the specificed amount of time

    Args:
        sock (socket): The socket to do al teh listening on
        ip (string): The ip address we are looking for
        done (Event): The event to trigger when we have finished
        retval (bool): Whether or not we have found the IP

    Returns:
        String[]: All the ARP ip addresses found in that time
    '''
    #found = []
    counter = 0
    # We can receive up to 3 IPs
    while not done.is_set():
        try: 
            raw = sock.recvfrom(2048)
        except Exception:
            return
        eth_header = raw[0][0:14]
        # Get the ethernet type
        eth_type = eth_header[-2:]
        #  Check if we are looking at an ARP packet (0x0806)
        if eth_type == b'\x08\x06':
            arp_header = raw[0][14:42]
            arp_type = arp_header[6:8]
            # look only at ARP replies
            if arp_type == b'\x00\x02':
                # Get the IP from the reply
                fip = socket.inet_ntoa(arp_header[14:18])
                # If its the one we are looking for, break
                if ip == fip:
                    retval += [True]
                    done.set()
                    break
        counter += 1


def send_arp(device, ip_src, ip_dst, mac_src=None):
    '''
    Send an ARP request to the given raw socket
    Args:
        sock (socket.socket): The raw socket to send the data to
        ip_src (string): The source IP address
        ip_dst (string): The destination IP address as a string.
        mac_src (bytes, optional): The source MAC address as a byte string
    Returns:
        bool:   Whether or not the arp packet was sent
    '''
    # Create raw socket
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.SOCK_RAW)
    # Bind to the interface given
    sock.bind((device, socket.SOCK_RAW))
    if not mac_src:
        mac_src = sock.getsockname()[4]  # Get the mac from socket (in binary)
    # Pack everything together into a packet
    FRAME = (
    b'\xFF\xFF\xFF\xFF\xFF\xFF' +           # Broadcast mac
    mac_src +                               # Source MAC
    b'\x08\x06' +                           # Type: ARP
    b'\x00\x01' +                           # Hardware type: ethernet
    b'\x08\x00' +                           # Protocol: TCP
    b'\x06' +                               # Hardware Size: 6 bytes
    b'\x04' +                               # Protocol Szie: 4 bytes
    b'\x00\x01' +                           # OpCode: Arp Request
    mac_src +                               # Sender MAC
    socket.inet_aton(ip_src) +              # Sender IP
    b'\x00\x00\x00\x00\x00\x00' +           # A blank mac
    socket.inet_aton(ip_dst)                # Target IP
    )
    sock.send(FRAME)
    sock.close()

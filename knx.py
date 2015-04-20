#!/usr/bin/env python
# -*- coding: utf-8 -*-


import socket
import struct
from collections import namedtuple


EIB_OPEN_GROUPCON = 0x26
EIB_GROUP_PACKET = 0x27

KNXWRITE = 0x80


GroupAddress = namedtuple('GroupAddress', ['main', 'middle', 'sub'])


def read_group_addr(addr):
    """ converts a group address to an integer

    >>> read_group_addr('0/1/14')
    270

    >>> read_group_addr(GroupAddress(0, 1, 14))
    270

    See also: http://www.openremote.org/display/knowledge/KNX+Group+Address
    """
    def conv(main, middle, sub):
        return (int(main) << 11) + (int(middle) << 8) + int(sub)

    if isinstance(addr, str):
        parts = addr.split('/')
        if len(parts) == 3:
            return conv(parts[0], parts[1], parts[2])
    elif isinstance(addr, GroupAddress):
        return conv(addr.main, addr.middle, addr.sub)
    raise ValueError


def encode_data(fmt, data):
    """ encode the data using struct.pack

    >>> encoded = encode_data('HHB', (27, 1, 0))

    = ==================
    >   big endian
    H   unsigned integer
    B   unsigned char
    = ==================
    """
    ret = struct.pack('>' + fmt, *data)
    if len(ret) < 2 or len(ret) > 0xffff:
        raise ValueError('(encoded) data length needs to be between 2 and 65536')
    # prepend data length
    return struct.pack('>H', len(ret)) + ret


class Connection:
    def __init__(self, host, port):
        s = socket.socket()
        s.connect((host, port))
        s.send(encode_data('HHB', [EIB_OPEN_GROUPCON, 0, 0]))
        self._socket = s

    def write(self, addr, value):
        addr = read_group_addr(addr)
        self._socket.send(
            encode_data('HHBB', [EIB_GROUP_PACKET, addr ,0 , KNXWRITE | value]))

    def close(self):
        self._socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()



def connect(host='localhost', port=6720):
    return Connection(host, port)

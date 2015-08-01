#!/usr/bin/env python
# -*- coding: utf-8 -*-


import asyncio
import socket
import struct
from collections import namedtuple


EIB_OPEN_GROUPCON = 0x26
EIB_GROUP_PACKET = 0x27

KNXWRITE = 0x80
KNXREAD = 0x00


GroupAddress = namedtuple('GroupAddress', ['main', 'middle', 'sub'])
Telegram = namedtuple('Telegram', ['src', 'dst', 'value'])


def encode_ga(addr):
    """ converts a group address to an integer

    >>> encode_ga('0/1/14')
    270

    >>> encode_ga(GroupAddress(0, 1, 14))
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


def decode_ga(ga):
    """ decodes a group address back into its human readable string representation

    >>> decode_ga(270)
    '0/1/14'
    """
    if not isinstance(ga, int):
        ga = struct.unpack('>H', ga)[0]
    return '{}/{}/{}'.format((ga >> 11) & 0x1f, (ga >> 8) & 0x07, (ga) & 0xff)


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


def coroutine(func):
    """ decorator to create a coroutine

    >>> @coroutine
    ... def logger():
    ...     while True:
    ...         line = (yield)
    ...         print(line)
    """
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.send(None)
        return cr
    return start


@coroutine
def telegram_decoder(target=None):
    """ a coroutine that receives binary telegrams and forwards them decoded

    :param target:
        another coroutine that will receive the decoded telegrams (as
        ``Telegram`` namedtuple)

    the binary telegram is in the following format:
        2 byte: length
        2 byte: type
        2 byte: src
        2 byte: dst
        2 byte: command data
    """
    buf = b''
    num_read = 0
    while True:
        data = (yield)
        num_read += len(data)
        buf += data
        if num_read < 4:
            continue
        ttype = (buf[2] << 8 | buf[3])
        if ttype != 39 or len(buf) < 6:
            buf = b''
            num_read = 0
            continue

        src = decode_ga(buf[4] << 8 | buf[5])
        dst = decode_ga(buf[6] << 8 | buf[7])
        data = buf[8:]
        if data[1] & 0xC0:
            value = str(data[1] & 0x3F)
        else:
            value = '?'

        target.send(Telegram(src, dst, value))
        num_read = 0
        buf = b''


def write(writer, addr, value):
    """ send a KNXWRITE request to the given group addr

    :param writer:
        a StreamWriter or other obj that has a ``write`` method.
        It is possible to use SocketWriterAdapter to wrap a socket so that it
        has a ``write`` method which just calls ``send`` on the socket.

    :param addr:
        The group addr to which the telegram should be sent to.
        Might be a GroupAddress named tuple or string. E.g. '0/1/14'

    :param value:
        The value to sent. Either 1 or 0

    """

    if isinstance(addr, (str, GroupAddress)):
        addr = encode_ga(addr)
    if isinstance(value, str):
        value = int(value)
    writer.write(
        encode_data('HHBB', [EIB_GROUP_PACKET, addr, 0, KNXWRITE | value]))


def read(writer, addr):
    """ send a read request to the given address

    this will instruct the bus system to send a telegram with the current
    value.

    In order to catch that telegram the ``AsyncKnx`` class has to be used.
    See ``examples/example_async_knx.py``

    So this means:

        read(writer, '0/0/20')

    Will cause the knx listener to retrieve 2 telegrams:

    Telegram(src='0/0/0', dst='0/0/20', value='?')
    Telegram(src='2/1/1', dst='0/0/20', value='1')

    """
    if isinstance(addr, (str, GroupAddress)):
        addr = encode_ga(addr)
    writer.write(
        encode_data('HHBB', [EIB_GROUP_PACKET, addr, 0, KNXREAD]))


class SocketWriterAdapter:
    def __init__(self, socket):
        self._socket = socket

    def write(self, data):
        self._socket.send(data)


class Connection:
    def __init__(self, host='localhost', port=6720):
        s = socket.socket()
        s.connect((host, port))
        s.send(encode_data('HHB', [EIB_OPEN_GROUPCON, 0, 0]))
        self.socket = s
        self.writer = SocketWriterAdapter(s)

    def write(self, addr, value):
        """ write to the given group address, see :func:`~knx.write`"""

        write(self.writer, addr, value)

    def read(self, addr):
        """ Calls :func:`knx.read` using the connections writer. """
        read(self.writer, addr)

    def close(self):
        self.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncKnx:
    def __init__(self, host='localhost', port=6720):
        self.host = host
        self.port = port
        self.writer = None
        self.reader = None

    @asyncio.coroutine
    def connect(self):
        self.reader, self.writer = yield from \
            asyncio.open_connection(self.host, self.port)
        self.writer.write(encode_data('HHB', [EIB_OPEN_GROUPCON, 0, 0]))

    @asyncio.coroutine
    def listen(self, receiver, decoder=telegram_decoder):
        """ start to receive data from the StreamReader and forward it decoded
        to the receiver

        :param receiver:
            a coroutine that will receive ``Telegram``s
        :param decoder:
            a function that takes one argument (which will be the given
            receiver) and returns a coroutine.  The coroutine will be fed
            binary telegrams.  The default decoder decodes those binary
            telegrams into ``Telegram`` namedtuples and forwards them to the
            receiver
        """
        if not self.reader:
            yield from self.connect()

        decoder = decoder(receiver)
        while True:
            data = yield from self.reader.read(100)
            decoder.send(data)

    @asyncio.coroutine
    def write(self, addr, value):
        """ write to the given group address, see :func:`~knx.write`"""

        if not self.writer:
            yield from self.connect()
        yield from write(self.writer, addr, value)

    def close(self):
        if self.writer:
            self.writer.close()


def connect(host='localhost', port=6720):
    return Connection(host, port)

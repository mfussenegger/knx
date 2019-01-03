#!/usr/bin/env python3


import asyncio as aio
import socket
import struct
from typing import NamedTuple, Any, Union, Iterable, Callable


EIB_OPEN_GROUPCON = 0x26
EIB_GROUP_PACKET = 0x27

KNXWRITE = 0x80
KNXREAD = 0x00


class GroupAddress(NamedTuple):
    main: int
    middle: int
    sub: int


class Telegram(NamedTuple):
    src: str
    dst: str
    value: Any


def encode_ga(addr: Union[str, GroupAddress]) -> int:
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


def decode_ia(ia: int) -> str:
    """ Decode an individual address into human readable string representation

    >>> decode_ia(4606)
    '1.1.254'

    See also: http://www.openremote.org/display/knowledge/KNX+Individual+Address
    """
    if not isinstance(ia, int):
        ia = struct.unpack('>H', ia)[0]
    return '{}.{}.{}'.format((ia >> 12) & 0x1f, (ia >> 8) & 0x07, (ia) & 0xff)


def decode_ga(ga: int) -> str:
    """ Decodes a group address into human readable string representation

    >>> decode_ga(270)
    '0/1/14'
    """
    if not isinstance(ga, int):
        ga = struct.unpack('>H', ga)[0]
    return '{}/{}/{}'.format((ga >> 11) & 0x1f, (ga >> 8) & 0x07, (ga) & 0xff)


def encode_data(fmt: str, data: Iterable) -> bytes:
    r""" encode the data using struct.pack

    >>> encode_data('HHB', (27, 1, 0))
    b'\x00\x05\x00\x1b\x00\x01\x00'

    = ==================
    >   big endian
    H   unsigned integer
    B   unsigned char
    = ==================
    """
    ret = struct.pack('>' + fmt, *data)
    if len(ret) < 2 or len(ret) > 0xffff:
        raise ValueError('Encoded data length needs to be between 2 and 65536')
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


def _decode(buf: bytearray) -> Telegram:
    """ decodes a binary telegram in the format:

        2 byte: src
        2 byte: dst
        X byte: data

    Returns a Telegram namedtuple.

    For read requests the value is -1
    If the data had only 1 bytes the value is either 0 or 1
    In case there was more than 1 byte the value will contain the raw data as
    bytestring.

    >>> _decode(bytearray([0x11, 0xFE, 0x00, 0x07, 0x00, 0x83]))
    Telegram(src='1.1.254', dst='0/0/7', value=3)

    >>> _decode(bytearray([0x11, 0x08, 0x00, 0x14, 0x00, 0x81]))
    Telegram(src='1.1.8', dst='0/0/20', value=1)

    """
    src = decode_ia(buf[0] << 8 | buf[1])
    dst = decode_ga(buf[2] << 8 | buf[3])

    flg = buf[5] & 0xC0
    data = buf[5:]

    if flg == KNXREAD:
        value = -1
    elif len(data) == 1:
        value = data[0] & 0x3F
    else:
        value = data[1:]

    return Telegram(src, dst, value)


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
        X byte: command data
    """
    buf = bytearray()
    num_read = 0
    telegram_length = 2
    while True:
        data = (yield)
        num_read += len(data)
        buf.extend(data)
        if num_read < telegram_length:
            continue

        telegram_length = (buf[0] << 0 | buf[1])
        if num_read < telegram_length + 2:
            continue

        ttype = (buf[2] << 8 | buf[3])
        if ttype != 39 or len(buf) < 6:
            buf = bytearray()
            num_read = 0
            telegram_length = 2
            continue

        target.send(_decode(buf[4:]))

        telegram_length = 2
        num_read = 0
        buf = bytearray()


def encode_dt_bit(addr: int, value: Any) -> bytes:
    r""" Encode a bit (0/1)

    :param addr:
        A encoded GroupAddress

    :param value:
        The value to send

    >>> encode_dt_bit(encode_ga(GroupAddress(0, 1, 14)), 1)
    b"\x00\x06\x00'\x01\x0e\x00\x81"

    """
    return encode_data(
        'HHBB',
        (EIB_GROUP_PACKET, addr, 0, KNXWRITE | int(value))
    )


def write(writer,
          addr: Union[str, GroupAddress],
          value: Any,
          encode: Callable[[int, Any], bytes] = None):
    """ send a KNXWRITE request to the given group addr

    :param writer:
        a StreamWriter or other obj that has a ``write`` method.
        It is possible to use SocketWriterAdapter to wrap a socket so that it
        has a ``write`` method which just calls ``send`` on the socket.

    :param addr:
        The group addr to which the telegram should be sent to.
        Might be a GroupAddress named tuple or string. E.g. '0/1/14'

    :param value:
        The value to send.

    :param encode:
        The encode function used to encode the addr and value into a message.
        Defaults to `encode_dt_bit`.
        The function receives two arguments.
        The encoded group address and the value
    """
    if isinstance(addr, (str, GroupAddress)):
        addr = encode_ga(addr)
    encode = encode or encode_dt_bit
    writer.write(encode(addr, value))


def read(writer, addr):
    """ send a read request to the given address

    this will instruct the bus system to send a telegram with the current
    value.

    In order to catch that telegram the ``AsyncKnx`` class has to be used.
    See ``examples/example_async_knx.py``

    So this means:

        read(writer, '0/0/20')

    Will cause the knx listener to retrieve 2 telegrams:

    Telegram(src='0/0/0', dst='0/0/20', value=-1)
    Telegram(src='2/1/1', dst='0/0/20', value='1')

    """
    if isinstance(addr, (str, GroupAddress)):
        addr = encode_ga(addr)
    writer.write(
        encode_data('HHBB', (EIB_GROUP_PACKET, addr, 0, KNXREAD)))


async def listen(reader, receiver, decoder=telegram_decoder):
    decoder = decoder(receiver)
    while True:
        data = await reader.read(100)
        decoder.send(data)


async def open_connection(host, port, *args, **kwargs):
    reader, writer = await aio.open_connection(host, port, *args, **kwargs)
    writer.write(encode_data('HHB', (EIB_OPEN_GROUPCON, 0, 0)))
    return reader, writer


async def bus_monitor(receiver,
                      host='localhost',
                      port=6720,
                      decoder=telegram_decoder):
    """ creates a connection to host:port and starts to receive telegrams

    :param receiver: a coroutine or instance of a class that has a `send`
                     method which takes one argument to receive a telegram.
    :param host: hostname to which to connect to
    :param port: port to which to connect to
    :param decoder: optional alternative decoder to transform binary data into
                    telegrams

    received telegrams will be sent to the receiver.
    """
    reader, writer = await open_connection(host, port)
    await listen(reader, receiver, decoder)
    writer.close()


class SocketWriterAdapter:
    def __init__(self, socket):
        self._socket = socket

    def write(self, data):
        self._socket.send(data)


class Connection:
    def __init__(self, host='localhost', port=6720):
        s = socket.socket()
        self._host = host
        self._port = int(port)
        s.connect((host, int(port)))
        s.send(encode_data('HHB', (EIB_OPEN_GROUPCON, 0, 0)))
        self.socket = s
        self.writer = SocketWriterAdapter(s)

    def write(self, addr, value, encode=None):
        """ write to the given group address, see :func:`~knx.write`"""

        write(self.writer, addr, value, encode=encode)

    def read(self, addr):
        """ Calls :func:`knx.read` using the connections writer. """
        read(self.writer, addr)

    async def bus_monitor(self, receiver, decoder=telegram_decoder):
        await bus_monitor(
            receiver=receiver,
            host=self._host,
            port=self._port,
            decoder=decoder
        )

    def close(self):
        self.socket.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def connect(host='localhost', port=6720):
    return Connection(host, port)

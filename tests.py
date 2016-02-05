#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch
from doctest import DocTestSuite
import knx


@knx.coroutine
def f(output):
    while True:
        x = (yield)
        output.append(x)


class KnxTest(unittest.TestCase):
    def test_encode_ga(self):
        x = knx.encode_ga('0/1/14')
        self.assertEqual(270, x)

    def test_decode_ga(self):
        x = knx.decode_ga(270)
        self.assertEqual('0/1/14', x)

    def test_encode_data(self):
        d = knx.encode_data('HHB', (27, 1, 0))
        self.assertEqual(b'\x00\x05\x00\x1b\x00\x01\x00', d)

    def decode(self, b):
        output = []
        decoder = knx.telegram_decoder(f(output))
        decoder.send(b)
        return output

    def test_telegram_decoder_receiving_single_bytes(self):
        output = []
        decoder = knx.telegram_decoder(f(output))
        decoder.send(b'\x00')
        decoder.send(b'\x08')
        decoder.send(b'\x00')
        decoder.send(b'\x27')
        decoder.send(b'\x11')
        decoder.send(b'\xFE')
        decoder.send(b'\x00')
        decoder.send(b'\x07')
        decoder.send(b'\x00')
        decoder.send(b'\x83')

        self.assertEqual(1, len(output))
        decoded = output[0]
        self.assertEqual(decoded.src, '1.1.254')
        self.assertEqual(decoded.dst, '0/0/7')
        self.assertEqual(decoded.value, 3)

    def test_telegram_decoder_0(self):
        output = self.decode(b"\x00\x08\x00'\x11\x08\x00\x14\x00\x81")
        self.assertEqual(1, len(output))
        decoded = output[0]
        self.assertEqual(decoded.src, '1.1.8')
        self.assertEqual(decoded.dst, '0/0/20')
        self.assertEqual(decoded.value, 1)

    def test_telegram_decoder_1(self):
        output = self.decode(b'\x00\x08\x00\x27\x11\xFE\x00\x07\x00\x83')

        self.assertEqual(1, len(output))
        decoded = output[0]
        self.assertEqual(decoded.src, '1.1.254')
        self.assertEqual(decoded.dst, '0/0/7')
        self.assertEqual(decoded.value, 3)

    def test_telegram_decoder_2(self):
        output = self.decode(b'\x00\x0B\x00\x27\x11\xFE\x00\x07\x00\x80\x03\xA3\x03')

        self.assertEqual(1, len(output))
        decoded = output[0]
        self.assertEqual(decoded.src, '1.1.254')
        self.assertEqual(decoded.dst, '0/0/7')
        self.assertEqual(decoded.value, b'\x03\xA3\x03')

    def test_call_write_with_str_addr(self):
        writer = MagicMock()
        knx.write(writer, '0/0/20', 1)
        writer.write.assert_called_with(b"\x00\x06\x00'\x00\x14\x00\x81")

    def test_call_write_with_ga_addr(self):
        writer = MagicMock()
        knx.write(writer, knx.GroupAddress(0, 0, 20), '1')
        writer.write.assert_called_with(b"\x00\x06\x00'\x00\x14\x00\x81")

    def test_call_read(self):
        writer = MagicMock()
        knx.read(writer, knx.GroupAddress(0, 0, 20))
        writer.write.assert_called_with(b"\x00\x06\x00'\x00\x14\x00\x00")

    @patch('socket.socket')
    def test_connect_connects_to_socket(self, socket):
        sock = MagicMock()
        socket.return_value = sock
        with knx.connect('localhost'):
            sock.connect.assert_called_once_with(('localhost', 6720))
            sock.send.assert_called_once_with(b'\x00\x05\x00&\x00\x00\x00')
        sock.close.assert_called_with()


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(knx))
    return tests


if __name__ == "__main__":
    unittest.main()

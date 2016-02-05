#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, main
from doctest import DocTestSuite
import knx


@knx.coroutine
def f(output):
    while True:
        x = (yield)
        output.append(x)


class KnxTest(TestCase):
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


def load_tests(loader, tests, ignore):
    tests.addTests(DocTestSuite(knx))
    return tests


if __name__ == "__main__":
    main()

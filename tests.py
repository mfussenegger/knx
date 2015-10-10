#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, TestSuite, makeSuite
from doctest import DocTestSuite
from knx import (
    encode_ga,
    decode_ga,
    telegram_decoder,
    coroutine,
    encode_data
)


class KnxTest(TestCase):
    def test_encode_ga(self):
        x = encode_ga('0/1/14')
        self.assertEqual(270, x)

    def test_decode_ga(self):
        x = decode_ga(270)
        self.assertEqual('0/1/14', x)

    def test_encode_data(self):
        d = encode_data('HHB', (27, 1, 0))
        self.assertEqual(b'\x00\x05\x00\x1b\x00\x01\x00', d)

    def test_telegram_decoder(self):
        output = []

        @coroutine
        def f():
            while True:
                x = (yield)
                output.append(x)
        decoder = telegram_decoder(f())
        decoder.send(b"\x00\x08\x00'\x11\x08\x00\x14\x00\x81")

        self.assertEqual(1, len(output))
        decoded = output[0]
        self.assertEqual(decoded.src, '1.1.8')
        self.assertEqual(decoded.dst, '0/0/20')
        self.assertEqual(decoded.value, '1')



def test_suite():
    return TestSuite([
        makeSuite(KnxTest),
        DocTestSuite('knx')
    ])

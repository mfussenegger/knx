#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, TestSuite, makeSuite
from doctest import DocTestSuite
from knx import (
    read_group_addr,
    encode_data
)


class KnxTest(TestCase):
    def test_read_group_addr(self):
        x = read_group_addr('0/1/14')
        self.assertEqual(270, x)

    def test_encode_data(self):
        d = encode_data('HHB', (27, 1, 0))
        self.assertEqual(b'\x00\x05\x00\x1b\x00\x01\x00', d)


def test_suite():
    return TestSuite([
        makeSuite(KnxTest),
        DocTestSuite('knx')
    ])

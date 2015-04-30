#!/usr/bin/env python
# -*- coding: utf-8 -*-

from knx import connect


with connect('nuc') as c:
    c.write('0/0/20', 1)

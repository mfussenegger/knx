#!/usr/bin/env python

from knx import connect


with connect('nuc') as c:
    c.write('0/0/20', 1)

#!/usr/bin/env python
# -*- coding: utf-8 -*-


from knx import connect


with connect('nuc') as c:
    c.read('0/0/20')

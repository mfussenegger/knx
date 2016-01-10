#!/usr/bin/env python

from knx import connect

with connect('nuc') as c:
    # this only sends a request to the bus which "requests" the current state
    # the response from the bus is sent asynchronous and a bus_monitor/listener
    # has to be used to retrieve the actual state.

    # see examples/actor.py for an example which does that.
    c.read('0/0/20')

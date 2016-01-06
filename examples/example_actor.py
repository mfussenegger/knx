#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This is an example that makes use of all methods of the ``AsyncKnx`` class.

It is a command line application that can be used to toggle the state of a
single actor (a Light for example).
"""


import os
import signal
import asyncio
import argparse
from knx import AsyncKnx, read


class Actor:
    """ Represents an actor on the bus system

    It has a toggle function in order to change the state from 0 (off) to 1
    (on) and back again.
    """

    def __init__(self, address, write_func):
        """ create an actor

        :param address: The address of the actor in the bus system.
                        Something like '0/0/20'
        :param write_func: A reference to AsyncKnx.write
        """

        self.address = address
        self.write = write_func
        self.state = 0

    def toggle(self):
        newstate = 1 if self.state == 0 else 0
        print('Sending value: {value} to address: {address}'.format(
            value=newstate,
            address=self.address))

        # AsyncKnx.write is a asyncio.coroutine
        # ensure_future is required to schedule the execution, otherwise
        # toggle would have to be a asyncio.coroutine itself.
        # see https://docs.python.org/3/library/asyncio-task.html?highlight=ensure_future#asyncio.ensure_future
        asyncio.ensure_future(self.write(self.address, newstate))

    def send(self, telegram):
        """ This metod receives telegrams from the bus system.

        It uses the telegram to update the state of the actor.  This way
        toggle() will always do the right thing, even if the state of the actor
        has been changed without using toggle (E.g. by using a regular light
        switch)

        Further down in ``main()`` an instance of this ``Actor`` class is being
        passed to `AsyncKnx.listen`` as a ``receiver``.

        A ``receiver`` is any object that has a send method with one argument
        (the telegram).
        """

        if telegram.dst != self.address:
            # this telegram is for a different actor
            return
        if not isinstance(telegram.value, int):
            return
        value = int(telegram.value)
        if value < 0:
            # -1 are read requests
            return
        print('New state of Actor {address} is {value}'.format(
            address=self.address,
            value=value))
        self.state = value

    def __repr__(self):
        return 'Actor<{address}>'.format(address=self.address)


def parse_host_and_port(host):
    if ':' in host:
        return host.split(':')
    return host, 6720  # default port of EIBD


@asyncio.coroutine
def read_initial_state(knx, address):
    _, writer = yield from knx.connect()
    read(writer, address)


def main():
    # usage: python example_actor.py eibd_host[:port] actor_address
    # e.g. python example_actor.py localhost '0/0/20'
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str)
    parser.add_argument("actor", type=str)
    args = parser.parse_args()

    host, port = parse_host_and_port(args.host)
    print('Creating connection to {host}:{port}'.format(host=host, port=port))
    knx = AsyncKnx(host=host, port=port)
    actor = Actor(address=args.actor, write_func=knx.write)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGUSR1, actor.toggle)
    print('Use "kill -USR1 {pid}" to toggle state'.format(pid=os.getpid()))

    asyncio.ensure_future(read_initial_state(knx, actor.address))
    try:
        loop.run_until_complete(knx.listen(actor))
    except KeyboardInterrupt:
        print('Byte')
    finally:
        knx.close()
        loop.close()


if __name__ == "__main__":
    main()

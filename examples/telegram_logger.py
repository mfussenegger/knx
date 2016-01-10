#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import asyncio
from knx import bus_monitor, coroutine


@coroutine
def logger():
    while True:
        line = (yield)
        print(line)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('host', type=str)
    p.add_argument('-p', '--port', type=int, default=6720)

    args = p.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            bus_monitor(logger(), host=args.host, port=args.port))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()

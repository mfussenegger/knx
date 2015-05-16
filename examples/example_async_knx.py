#!/usr/bin/env python
# -*- coding: utf-8 -*-


import asyncio
from knx import AsyncKnx, coroutine


@coroutine
def logger():
    while True:
        line = (yield)
        print(line)


loop = asyncio.get_event_loop()
knx = AsyncKnx(host='nuc', port=6720)

try:
    loop.run_until_complete(knx.listen(logger()))
except KeyboardInterrupt:
    pass
finally:
    knx.close()
    loop.close()

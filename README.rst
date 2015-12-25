===
knx
===

.. image:: https://travis-ci.org/mfussenegger/knx.svg?branch=master
    :target: https://travis-ci.org/mfussenegger/knx
    :alt: travis-ci

.. image:: https://img.shields.io/pypi/wheel/knx.svg
    :target: https://pypi.python.org/pypi/knx/
    :alt: Wheel

.. image:: https://img.shields.io/pypi/v/knx.svg
   :target: https://pypi.python.org/pypi/knx/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/knx.svg
   :target: https://pypi.python.org/pypi/knx/
   :alt: Python Version


A minimalistic `KNX <https://en.wikipedia.org/wiki/KNX_%28standard%29>`_ / EIB
python library.


Sending telegrams
-----------------

This library can be used to send data telegrams to actuators in the bus system.

For example in order to turn on a light the following code could be used::

    >>> from knx import connect
    >>> with connect() as c:
    ...     c.write('0/1/14', 1)


Where ``0/1/14`` is the address of the light and ``1`` is the payload of the
data telegram which indicates that the light should be turned on.


Listening to telegrams
----------------------

This KNX library can also be used to listen to telegrams that are sent onto the
bus system. For example if you simply want to log an entry each time a light is
turned off or on::


    >>> import knx
    >>> import asyncio

    >>> @knx.coroutine
    ... def logger():
    ...     while True:
    ...         telegram = (yield)
    ...         print('Telegram from {0} sent to {1} with value: {2}'.format(
    ...               telegram.src, telegram.dst, telegram.value))

    >>> loop = asyncio.get_event_loop()
    >>> k = knx.AsyncKnx(host='localhost', port=6720)
    >>> loop.run_until_complete(k.listen(logger()))


Install & Requirements
======================

- Python >= 3.4

Install using pip::

    $ pip install knx

Disclaimer
==========

I've only tested this with `eibd
<http://www.auto.tuwien.ac.at/~mkoegler/index.php/eibd>`_ 0.0.5 as a gateway.


Alternatives
============

If you're looking for complete home automation solutions you might want to take
a look at `home-assistant <https://github.com/balloob/home-assistant>`_ or
`smarthome <https://github.com/mknx/smarthome>`_.

Development
===========

In order to setup a sandboxed development environment use buildout:

1. Create a virtual environment to have a python without any third-party
   packages in it's ``sys.path``: (Kinda Optional)::

    python -m venv .venv

2. Run ``bootstrap.py``::

    .venv/bin/python bootstrap.py

3. Run ``bin/buildout``::

    bin/buildout

Once these steps are done you'll be able to run tests using ``bin/test``.

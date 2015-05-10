===
knx
===

A minimalistic KNX / EIB python library. It can be used to send telegrams to
actors in the bus system::

    >>> from knx import connect
    >>> with connect() as c:
    ...     c.write('0/1/14', 1)

Or it can be used to listen to the traffic on the bus system::

    >>> @coroutine
    ... def logger():
    ...     while True:
    ...         telegram = (yield)
    ...         print(telegram.src)
    ...         print(telegram.dst)
    ...         print(telegram.value)

    >>> knx.listen(logger())

See the examples folder for a full working example.


Requirements
============

- Python 3.4


Disclaimer
==========

I've only tested this with `eibd
<http://www.auto.tuwien.ac.at/~mkoegler/index.php/eibd>`_ 0.0.5 as a gateway.


Development
===========

In order to setup a sandboxed development environment use buildout:

1. Create a virtual environment to have a python without any third-party
   packages in it's ``sys.path``: (Kinda Optional)::

    python -m venv .venv

2. Run ``bootstrap.py``::

   .venv/bin/python bootstrap.py

3. Run ``bin/buildout``:

::

   bin/buildout

Once these steps are done you'll be able to run tests using ``bin/test``.

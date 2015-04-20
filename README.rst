===
knx
===


This is going to be a minimalistic KNX / EIB python library::

    >>> from knx import connect
    >>> with connect() as c:
    ...     c.write('0/1/14', 1)


Unless you want to hurt yourself. Don't try to use this just yet.

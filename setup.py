#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


try:
    readme = open('README.rst', 'r').read()
except IOError:
    readme = ''


setup(
    name='knx',
    version='0.1.3',
    author='Mathias Fußenegger',
    author_email='pip@zignar.net',
    url='https://github.com/mfussenegger/knx',
    license='MIT',
    description='KNX / EIB library',
    long_description=readme,
    platforms=['any'],
    py_modules=['knx'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
    ]
)

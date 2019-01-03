#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


try:
    with open('README.rst', 'r', encoding='utf-8') as f:
        readme = f.read()
except IOError:
    readme = ''


setup(
    name='knx',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    test_suite='tests'
)

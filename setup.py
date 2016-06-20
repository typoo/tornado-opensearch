# coding: utf-8
import sys

from setuptools import setup

__version__ = '0.0.1'

if sys.version_info < (3, 5):
    raise DeprecationWarning('目前仅支持 Python 3.5')

install_requires = open("requirements.txt").read().split()

setup(
    name="torando-opensearch",
    version=__version__,
    description='OpenSearch Python bindings for Tornado.',
    license='MIT',
    author="shaung",
    author_email='_@shaung.org',
    packages=[
        'tornado_opensearch',
        'tornado_opensearch.test'
    ],
    install_requires=install_requires,
    tests_require=[],
    test_suite='torando_opensearch.test.all',
)

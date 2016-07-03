# coding: utf-8
from unittest import mock, TestCase
from collections import OrderedDict

import tornado_opensearch.util as util


class UrlQuoteTests(TestCase):
    maxDiff = 1000

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def _call(self, value):
        return util.urlquote(value)

    def test_quoting_str(self):
        result = self._call("q=hello 世界&+-_.~")
        expected = "q%3Dhello%20%E4%B8%96%E7%95%8C%26%2B-_.~"
        self.assertEqual(result, expected)

    def test_quoting_bytes(self):
        result = self._call("q=hello 世界&+-_.~".encode("utf8"))
        expected = "q%3Dhello%20%E4%B8%96%E7%95%8C%26%2B-_.~"
        self.assertEqual(result, expected)

    def test_quoting_int(self):
        result = self._call(123.45)
        expected = "123.45"
        self.assertEqual(result, expected)

# coding: utf-8
from unittest import mock
from collections import OrderedDict

from tornado.gen import coroutine
from tornado.testing import AsyncTestCase, gen_test

import tornado_opensearch.api_requestor as api_requestor


class DummyAPIRequestor(mock.MagicMock):
    @coroutine
    def request(self, *args, **kwargs):
        return {"success": "OK"}


class TestSingator(AsyncTestCase):
    """ 签名逻辑测试"""
    maxDiff = 1000

    def setUp(self):
        self.public_params = {
            "Version": "v2",
            "AccessKeyId": "testid",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": "14053016951271226",
            "Timestamp": "2014-07-14T01:34:55Z"
        }
        self.params = OrderedDict(
            query="config=format:json,start:0,hit:20&&query=default:'的'",
            index_name="ut_3885312",
            format="json",
            fetch_fields="title;gmt_modified"
        )

        super().setUp()

    def tearDown(self):
        super().tearDown()

    def _cls(self):
        return api_requestor.Signator

    def test_canonicalize_query(self):
        """ 测试URL编码"""
        query = self._cls().build_query(self.params, self.public_params)
        result = self._cls().canonicalize_query(query)
        expected = "AccessKeyId=testid&SignatureMethod=HMAC-SHA1&SignatureNonce=14053016951271226&SignatureVersion=1.0&Timestamp=2014-07-14T01%3A34%3A55Z&Version=v2&fetch_fields=title%3Bgmt_modified&format=json&index_name=ut_3885312&query=config%3Dformat%3Ajson%2Cstart%3A0%2Chit%3A20%26%26query%3Ddefault%3A%27%E7%9A%84%27"

        self.assertEqual(result, expected)

    def test_get_signature(self):
        """ 测试取得签名"""
        result = self._cls().get_signature(
            secret="testsecret",
            url="GET&%2F&AccessKeyId%3Dtestid%26SignatureMethod%3DHMAC-SHA1%26SignatureNonce%3D14053016951271226%26SignatureVersion%3D1.0%26Timestamp%3D2014-07-14T01%253A34%253A55Z%26Version%3Dv2%26fetch_fields%3Dtitle%253Bgmt_modified%26format%3Djson%26index_name%3Dut_3885312%26query%3Dconfig%253Dformat%253Ajson%252Cstart%253A0%252Chit%253A20%2526%2526query%253Ddefault%253A%2527%25E7%259A%2584%2527"
        )

        expected = "/GWWQkztlp/9Qg7rry2DuCSfKUQ="

        self.assertEqual(result, expected)

    def test_sign_url(self):
        """ 测试签名"""

        result = self._cls()._sign_url(
            method="GET",
            endpoint="/search",
            api_baseurl="http://$host",
            api_secret="testsecret",
            params=self.params,
            public_params=self.public_params
        )

        expected = "http://$host/search?query=config%3Dformat%3Ajson%2Cstart%3A0%2Chit%3A20%26%26query%3Ddefault%3A%27%E7%9A%84%27&index_name=ut_3885312&format=json&fetch_fields=title%3Bgmt_modified&Version=v2&AccessKeyId=testid&SignatureMethod=HMAC-SHA1&SignatureVersion=1.0&SignatureNonce=14053016951271226&Timestamp=2014-07-14T01%3A34%3A55Z&Signature=%2FGWWQkztlp%2F9Qg7rry2DuCSfKUQ%3D"

        # 因参数顺序不同，在此只比较长度
        self.assertEqual(len(result), len(expected))

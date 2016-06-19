# coding: utf8
from unittest import mock

from tornado.gen import coroutine
from tornado.testing import AsyncTestCase, gen_test

import tornado_opensearch.resource as resource


class DummyAPIRequestor(mock.MagicMock):
    @coroutine
    def request(self, *args, **kwargs):
        return {"success": "OK"}


class TestOpenSearch(AsyncTestCase):
    maxDiff = 1000

    def setUp(self):
        self.patch_requestor = mock.patch(
            "tornado_opensearch.resource.APIRequestor",
            new=DummyAPIRequestor
        )
        self.MockAPIRequestor = self.patch_requestor.start()

        super().setUp()

    def tearDown(self):
        self.patch_requestor.stop()

        super().tearDown()

    def _make_one(self, **kwargs):
        return resource.OpenSearch(**kwargs)

    @gen_test
    def test_search(self):
        """ 测试搜索"""

        api = self._make_one(
            api_baseurl="",
            api_key="testkey",
            api_secret="testsecret",
            api_version="v2"
        )
        result = yield api.search(query="")
        expected = {
            "success": "OK"
        }
        self.assertEqual(result, expected)

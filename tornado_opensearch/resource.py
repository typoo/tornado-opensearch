# coding: utf-8
import json

import tornado
from tornado.gen import coroutine

from tornado_opensearch.api_requestor import APIRequestor
from tornado_opensearch import util


API_VERSION = "v2"


class APIResource(object):
    def __init__(self, **kwargs):
        self.api_baseurl = kwargs.get("api_baseurl")
        self.api_key = kwargs.get("api_key")
        self.api_secret = kwargs.get("api_secret")
        self.api_version = kwargs.get("api_version") or API_VERSION

        self.app_name = kwargs.get("app_name")

    @coroutine
    def request(self, *args, **kwargs):
        requestor = APIRequestor(
            self.api_baseurl,
            self.api_key,
            self.api_secret,
            self.api_version
        )

        response = yield requestor.request(*args, **kwargs)
        return response


class OpenSearch(APIResource):
    """ OpenSearch v2 API """

    def run_sync(self, name, *args, **kwargs):
        func = getattr(self, name, None)
        if not func:
            return

        def wrapped():
            kwargs["callback"] = print
            return func(*args, **kwargs)

        return tornado.ioloop.IOLoop.current().run_sync(wrapped)

    def _pair(self, dct):
        if not dct:
            return None

        if hasattr(dct, "items"):
            return ",".join(
                "%s:%s" % (k, v) for (k, v) in dct.items()
            )

        return dct

    def make_query_str(self, dct):
        clauses = {
            k: self._pair(v) for k, v in dct.items()
        }

        query_str = "&&".join(
            "%s=%s" % (k, v) for k, v in clauses.items() if v
        )
        return query_str

    @coroutine
    def search(self, query, index_name=None, fetch_fields=""):
        """ 搜索"""
        endpoint = "/search"

        if hasattr(query, "items"):
            # 如果不是直接指定字符串，需要拼装搜索子句。
            query_str = self.make_query_str(query)
        else:
            query_str = query

        params = {
            "query": query_str,
            "index_name": index_name or self.app_name,
            "fetch_fields": fetch_fields,
            "format": "json",
        }
        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def suggest(self, query, suggest_name, index_name=None, hit=None):
        """ 下拉提示"""
        endpoint = "/suggest"

        params = {
            "query": query,
            "index_name": index_name or self.app_name,
            "suggest_name": suggest_name,
        }

        if hit is not None:
            params["hit"] = hit

        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def upload_data(self, table_name, items, app_name=None):
        """ 上传数据"""
        endpoint = "/index/doc/" + (app_name or self.app_name)
        params = {
            "action": "push",
            "table_name": table_name,
        }
        body = "items=" + util.urlquote(json.dumps(items))
        result = yield self.request(
            method="POST",
            endpoint=endpoint,
            params=params,
            body=body
        )
        return result

    @coroutine
    def list_apps(self, page=1, page_size=10):
        """ 取得应用列表"""
        endpoint = "/index"

        params = {
            "page": page,
            "page_size": page_size,
        }

        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def get_app(self, app_name=None):
        """ 取得应用信息"""
        endpoint = "/index/" + (app_name or self.app_name)

        params = {"action": "status"}

        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def create_app(self, template="", app_name=None):
        """ 创建应用（仅支持从模版创建）"""
        endpoint = "/index/" + (app_name or self.app_name)

        params = {
            "action": "create",
            "template": template,
        }

        result = yield self.request(
            method="POST",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def delete_app(self, app_name=None):
        """ 删除应用"""
        endpoint = "/index/" + (app_name or self.app_name)

        params = {"action": "delete"}

        result = yield self.request(
            method="POST",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def rebuild_index(self, table_names=(), app_name=None):
        """ 索引重建"""
        endpoint = "/index/" + (app_name or self.app_name)

        params = {
            "action": "createtask"
        }

        if table_names:
            params.update({
                "operate": "import",
                "table_name": ";".join(table_names),
            })

        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

    @coroutine
    def get_error_log(self, page=1, page_size=20,
                      sort_mode="DESC", app_name=None):
        """ 取得错误日志"""
        endpoint = "/index/error/" + (app_name or self.app_name)

        params = {
            "page": page,
            "page_size": page_size,
            "sort_mode": sort_mode,
        }
        result = yield self.request(
            method="GET",
            endpoint=endpoint,
            params=params
        )
        return result

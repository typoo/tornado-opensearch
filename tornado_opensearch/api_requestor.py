# coding: utf-8
from datetime import datetime, timezone
import time
import hmac
import base64
import random
import json
import operator
import logging

import tornado
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient

from tornado_opensearch import error
from tornado_opensearch import util


logger = logging.getLogger("tornado_opensearch")


class Signator(object):
    """ 签名逻辑"""

    @classmethod
    def _sign_url(cls, method, endpoint,
                  api_baseurl, api_secret,
                  params=None, public_params=None):
        """ 对URL进行签名"""

        query = cls.build_query(params, public_params)
        canonicalized = cls.canonicalize_query(query)

        url_to_sign = "%s&%s&%s" % (
            method.upper(),
            util.urlquote("/"),
            util.urlquote(canonicalized)
        )

        signature = cls.get_signature(api_secret, url_to_sign)

        # TODO: Use urlparse
        url = "%s%s?%s&Signature=%s" % (
            api_baseurl.rstrip("/"),
            endpoint,
            canonicalized,
            util.urlquote(signature)
        )
        return url

    @classmethod
    def build_public_params(cls, api_version, api_key,
                            nonce=None, timestamp=None, sign_mode=None):
        """ 构建公共参数。"""
        if not timestamp:
            # FIXME: timestamp "2014-07-14T01:34:55Z"
            utcnow = datetime.now(timezone.utc)
            timestamp = utcnow.isoformat().split(".")[0] + "Z"

        params = {
            "Version": api_version,
            "AccessKeyId": api_key,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": nonce or cls.get_nonce(),
            "Timestamp": timestamp,
        }

        if sign_mode is not None:
            # XXX: 这个参数在文档中未注明，但如果不加，POST 的签名会出错
            params["sign_mode"] = sign_mode

        return params

    @staticmethod
    def build_query(params=None, public_params=None):
        """ 构建请求字典"""
        if not public_params:
            public_params = {}

        if not params:
            params = {}

        if "format" not in params:
            params["format"] = "json"

        params = dict(public_params, **params)
        return params

    @staticmethod
    def canonicalize_query(query):
        """ 用于签名。
        1. 对所有请求参数排序
        2. 对每个参数的名称和值分别编码
        3. 拼装
        """
        return "&".join(
            "%s=%s" % (util.urlquote(k), util.urlquote(v))
            for k, v in sorted(
                query.items(),
                key=operator.itemgetter(0)
            )
        )

    @staticmethod
    def get_signature(secret, url):
        """ 取得签名"""
        mac = hmac.new(
            key=b"%s&" % secret.encode("utf-8"),
            msg=url.encode("utf-8"),
            digestmod="SHA1"
        )
        signature = base64.b64encode(mac.digest())
        return signature.decode("utf-8")

    @staticmethod
    def get_nonce():
        """ 17 位随机ID，每次请求必须不同"""
        return "%s%s" % (
            str(time.time()).replace(".", "")[:13],
            random.getrandbits(4)
        )


class APIRequestor(Signator):
    """ 请求"""

    def __init__(self, api_baseurl="", api_key=None, api_secret=None,
                 api_version=None, client=None, debug=False):
        self.api_baseurl = api_baseurl
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_version = api_version
        self.debug = debug

        self._client = client or AsyncHTTPClient()

    @coroutine
    def request(self, method, endpoint, params, body=""):
        """ 发起请求，对结果做预处理后返回 Response 字典。
        """
        raw_response = yield self.request_raw(method, endpoint, params, body)

        self.log_request(raw_response)

        response = self.parse_response(raw_response)

        return response

    @coroutine
    def request_raw(self, method, endpoint, params, body=""):
        """ 返回原始请求。"""
        response = None
        method = method.upper()

        if method == "GET":
            response = yield self._get(endpoint, params)
        elif method == "POST":
            response = yield self._post(endpoint, params, body)
        else:
            raise error.APIError("Bad request method")

        return response

    def parse_response(self, raw_response):
        """ 解析请求结果并处理错误。"""
        try:
            response = json.loads(raw_response.body.decode("utf-8"))
            code = raw_response.code
        except Exception as e:
            raise error.APIError("无法解析应答格式")

        if not (200 <= code < 400):
            raise error.APIError("请求失败 status: %s" % code)

        status = response.get("status", None)
        if status != "OK":
            errcode, errmsg = None, None
            for item in response.get("errors", ()):
                errcode = item.get("code")
                errmsg = item.get("message", "")

            message = self._format_error_message(errcode, errmsg)

            if errcode == 4003:
                raise error.InvalidSignature(message)
            elif errcode == 5001:
                raise error.AccessRestricted(message)
            else:
                raise error.APIError(message)

        return response

    def log_request(self, response):
        """ 记录请求时间"""
        if response.code < 400:
            log_method = logger.info
        elif response.code < 500:
            log_method = logger.warning
        else:
            log_method = logger.error
        request_time = 1000.0 * response.request_time
        log_method("%d %s %.2fms", response.code,
                   response.effective_url, request_time)

    @staticmethod
    def _format_error_message(code, message):
        return "code:%s, message:%s" % (code, message)

    @coroutine
    def _get(self, endpoint, params):
        url = self.sign_url(method="GET", endpoint=endpoint, params=params)
        request = tornado.httpclient.HTTPRequest(url=url)
        response = yield self._client.fetch(request)
        return response

    @coroutine
    def _post(self, endpoint, params, body):
        url = self.sign_url(method="POST", endpoint=endpoint, params=params)

        self._trace(body)

        request = tornado.httpclient.HTTPRequest(
            method="POST", url=url, body=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        response = yield self._client.fetch(request)
        return response

    def sign_url(self, method, endpoint, params=None, public_params=None):
        """ 返回签名后的URL"""
        if not public_params:
            public_params = self.build_public_params(
                self.api_version, self.api_key,
                sign_mode=(method == "POST" and 1 or None)
            )

        return self._sign_url(
            api_baseurl=self.api_baseurl,
            api_secret=self.api_secret,
            method=method,
            endpoint=endpoint,
            params=params,
            public_params=public_params
        )

    def _trace(self, *args):
        if self.debug:
            for x in args:
                logger.debug(x)
